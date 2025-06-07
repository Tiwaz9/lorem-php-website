import json
import os
from datetime import datetime, timezone
import time

import boto3
from botocore.exceptions import ClientError

# DynamoDB table name
DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME", "NetworkInventory")

ec2 = boto3.client("ec2")
dynamodb = boto3.client("dynamodb")


def iso_timestamp_now():
    """Return current UTC time as an ISO‐formatted string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def format_tags(tag_list):
    if not tag_list:
        return {"L": []}
    dynamo_tags = []
    for t in tag_list:
        dynamo_tags.append({
            "M": {
                "Key":   {"S": t.get("Key", "")},
                "Value": {"S": t.get("Value", "")}
            }
        })
    return {"L": dynamo_tags}


def build_vpc_items(vpcs, now_iso):
    items = []
    for vpc in vpcs:
        vpc_id = vpc.get("VpcId")
        pk = f"VPC#{vpc_id}"
        sk = "METADATA"
        item = {
            "PK":           {"S": pk},
            "SK":           {"S": sk},
            "ResourceType": {"S": "VPC"},
            "VpcId":        {"S": vpc_id},
            "CidrBlock":    {"S": vpc.get("CidrBlock", "")},
            "IsDefault":    {"BOOL": vpc.get("IsDefault", False)},
            "Tags":         format_tags(vpc.get("Tags", [])),
            "RetrievedAt":  {"S": now_iso},
        }
        items.append({"PutRequest": {"Item": item}})
    return items


def build_subnet_items(subnets, now_iso):
    items = []
    for sn in subnets:
        subnet_id = sn.get("SubnetId")
        vpc_id    = sn.get("VpcId")
        pk        = f"VPC#{vpc_id}"
        sk        = f"SUBNET#{subnet_id}"
        item = {
            "PK":               {"S": pk},
            "SK":               {"S": sk},
            "ResourceType":     {"S": "Subnet"},
            "SubnetId":         {"S": subnet_id},
            "VpcId":            {"S": vpc_id},
            "CidrBlock":        {"S": sn.get("CidrBlock", "")},
            "AvailabilityZone": {"S": sn.get("AvailabilityZone", "")},
            "MapPublicIpOnLaunch": {"BOOL": sn.get("MapPublicIpOnLaunch", False)},
            "Tags":             format_tags(sn.get("Tags", [])),
            "RetrievedAt":      {"S": now_iso},
        }
        items.append({"PutRequest": {"Item": item}})
    return items


def batch_write(table_name, put_requests):
    MAX_BATCH = 25
    chunks = [put_requests[i:i+MAX_BATCH] for i in range(0, len(put_requests), MAX_BATCH)]
    for idx, chunk in enumerate(chunks):
        request_items = {table_name: chunk}
        attempt = 0
        while True:
            try:
                resp = dynamodb.batch_write_item(RequestItems=request_items)
                unproc = resp.get("UnprocessedItems", {})
                if not unproc.get(table_name):
                    break
                request_items = unproc
                attempt += 1
                if attempt > 5:
                    print(f"Warning: too many retries for batch {idx}. Unprocessed: {unproc}")
                    break
                time.sleep(2 ** attempt)
            except ClientError as e:
                print(f"Error in batch_write_item: {e}")
                raise


def lambda_handler(event, context):
    now_iso = iso_timestamp_now()

    # Describe VPCs
    try:
        vpcs = ec2.describe_vpcs().get("Vpcs", [])
    except ClientError as e:
        print(f"DescribeVpcs failed: {e}")
        return proxy_response(500, {"error": str(e)})

    # Describe Subnets
    try:
        subnets = ec2.describe_subnets().get("Subnets", [])
    except ClientError as e:
        print(f"DescribeSubnets failed: {e}")
        return proxy_response(500, {"error": str(e)})

    # Build items
    vpc_items    = build_vpc_items(vpcs, now_iso)
    subnet_items = build_subnet_items(subnets, now_iso)
    all_items    = vpc_items + subnet_items

    if all_items:
        try:
            batch_write(DDB_TABLE_NAME, all_items)
        except Exception as e:
            print(f"DynamoDB write failed: {e}")
            return proxy_response(500, {"error": str(e)})

    # Success payload
    body = {
        "message":     "Inventory saved",
        "vpcCount":    len(vpcs),
        "subnetCount": len(subnets),
        "writtenItems": len(all_items),
        "timestamp":   now_iso
    }
    return proxy_response(200, body)


def proxy_response(status_code, body_obj):
    """Helper to build an AWS_PROXY–compatible response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type":                 "application/json",
            "Access-Control-Allow-Origin":  "*"
        },
        "body": json.dumps(body_obj)
    }
