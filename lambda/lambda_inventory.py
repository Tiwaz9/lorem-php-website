import json
import os
import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError

# DynamoDB table name
DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME", "NetworkInventory")

# AWS clients
ec2 = boto3.client("ec2")
dynamodb = boto3.client("dynamodb")


def iso_timestamp_now():
    """Return current UTC time as an ISO-formatted string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_tags(tag_list):
    """Convert AWS tags into DynamoDB-friendly list of key/value dicts."""
    if not tag_list:
        return []
    return [{"Key": t.get("Key", ""), "Value": t.get("Value", "")} for t in tag_list]


def build_vpc_items(vpcs, now_iso):
    """Prepare DynamoDB write requests for VPCs."""
    items = []
    for vpc in vpcs:
        pk = f"VPC#{vpc.get('VpcId')}"
        sk = "METADATA"
        item = {
            "PK": {"S": pk},
            "SK": {"S": sk},
            "ResourceType": {"S": "VPC"},
            "VpcId": {"S": vpc.get('VpcId', '')},
            "CidrBlock": {"S": vpc.get('CidrBlock', '')},
            "IsDefault": {"BOOL": vpc.get('IsDefault', False)},
            "Tags": {"L": [{"M": {"Key": {"S": tag['Key']}, "Value": {"S": tag['Value']}}} for tag in vpc.get('Tags', [])]},
            "RetrievedAt": {"S": now_iso}
        }
        items.append({"PutRequest": {"Item": item}})
    return items


def build_subnet_items(subnets, now_iso):
    """Prepare DynamoDB write requests for Subnets."""
    items = []
    for sn in subnets:
        pk = f"VPC#{sn.get('VpcId')}"
        sk = f"SUBNET#{sn.get('SubnetId')}"
        item = {
            "PK": {"S": pk},
            "SK": {"S": sk},
            "ResourceType": {"S": "Subnet"},
            "SubnetId": {"S": sn.get('SubnetId', '')},
            "VpcId": {"S": sn.get('VpcId', '')},
            "CidrBlock": {"S": sn.get('CidrBlock', '')},
            "AvailabilityZone": {"S": sn.get('AvailabilityZone', '')},
            "MapPublicIpOnLaunch": {"BOOL": sn.get('MapPublicIpOnLaunch', False)},
            "Tags": {"L": [{"M": {"Key": {"S": tag['Key']}, "Value": {"S": tag['Value']}}} for tag in sn.get('Tags', [])]},
            "RetrievedAt": {"S": now_iso}
        }
        items.append({"PutRequest": {"Item": item}})
    return items


def batch_write(table_name, put_requests):
    """Write items to DynamoDB in batches of 25 with retry."""
    MAX_BATCH = 25
    chunks = [put_requests[i:i+MAX_BATCH] for i in range(0, len(put_requests), MAX_BATCH)]
    for batch in chunks:
        request_items = {table_name: batch}
        attempt = 0
        while True:
            resp = dynamodb.batch_write_item(RequestItems=request_items)
            unproc = resp.get('UnprocessedItems', {})
            if not unproc.get(table_name):
                break
            request_items = unproc
            attempt += 1
            if attempt > 5:
                print(f"Too many retries for batch {batch}")
                break
            time.sleep(2 ** attempt)


def proxy_response(status_code, body_obj):
    """Helper to build a Lambda proxy response with CORS."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body_obj)
    }


def lambda_handler(event, context):
    """
    Describe VPCs & Subnets, write to DynamoDB, and return full details.
    Includes debug logging to CloudWatch to verify the payload.
    """
    now_iso = iso_timestamp_now()
    print(f"[DEBUG] Lambda invoked at {now_iso}")

    # Describe VPCs
    try:
        vpcs = ec2.describe_vpcs().get('Vpcs', [])
    except ClientError as e:
        return proxy_response(500, {"error": str(e)})

    # Describe Subnets
    try:
        subnets = ec2.describe_subnets().get('Subnets', [])
    except ClientError as e:
        return proxy_response(500, {"error": str(e)})

    # Persist to DynamoDB
    vpc_items = build_vpc_items(vpcs, now_iso)
    subnet_items = build_subnet_items(subnets, now_iso)
    all_items = vpc_items + subnet_items
    if all_items:
        batch_write(DDB_TABLE_NAME, all_items)

    # Build response payload including full resource arrays
    payload = {
        "message":       "Inventory saved",
        "vpcCount":      len(vpcs),
        "subnetCount":   len(subnets),
        "writtenItems":  len(all_items),
        "timestamp":     now_iso,
        "vpcs":          vpcs,
        "subnets":       subnets
    }

    print(f"[DEBUG] Payload: {json.dumps(payload)}")
    return proxy_response(200, payload)
