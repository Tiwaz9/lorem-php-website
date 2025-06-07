import json
import os
from datetime import datetime, timezone
import time

import boto3
from botocore.exceptions import ClientError

# DynamoDB table name (optional if writing inventory)
DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME", "NetworkInventory")

# AWS clients
ec2 = boto3.client("ec2")
dynamodb = boto3.client("dynamodb")


def iso_timestamp_now():
    """Return current UTC time as an ISO-formatted string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def proxy_response(status_code, body_obj):
    """Helper to build an AWS_PROXY-compatible response with CORS."""
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
    1) Describe all VPCs and Subnets
    2) (Optional) Persist inventory to DynamoDB
    3) Return full details of resources in JSON
    """
    timestamp = iso_timestamp_now()

    # Fetch VPCs
    try:
        vpc_response = ec2.describe_vpcs()
        vpcs = vpc_response.get("Vpcs", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeVpcs failed: {e}"})

    # Fetch Subnets
    try:
        subnet_response = ec2.describe_subnets()
        subnets = subnet_response.get("Subnets", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeSubnets failed: {e}"})

    # Optional: Write to DynamoDB
    # items = []
    # for v in vpcs:
    #     items.append({"PutRequest": {"Item": {"PK": {"S": f"VPC#${v['VpcId']}", ...}}}})
    # batch_write(DDB_TABLE_NAME, items)

    # Build detailed payload
    payload = {
        "timestamp":   timestamp,
        "vpcCount":    len(vpcs),
        "subnetCount": len(subnets),
        "vpcs":        [],
        "subnets":     []
    }
    # Populate VPC details
    for v in vpcs:
        payload["vpcs"].append({
            "VpcId":   v.get("VpcId"),
            "CidrBlock": v.get("CidrBlock"),
            "State":    v.get("State"),
            "IsDefault": v.get("IsDefault"),
            **({"Tags": v.get("Tags", [])} if v.get("Tags") is not None else {})
        })

    # Populate Subnet details
    for s in subnets:
        payload["subnets"].append({
            "SubnetId":               s.get("SubnetId"),
            "VpcId":                  s.get("VpcId"),
            "CidrBlock":              s.get("CidrBlock"),
            "AvailabilityZone":       s.get("AvailabilityZone"),
            "State":                  s.get("State"),
            "AvailableIpAddressCount": s.get("AvailableIpAddressCount"),
            "DefaultForAz":           s.get("DefaultForAz"),
            "MapPublicIpOnLaunch":    s.get("MapPublicIpOnLaunch"),
            **({"Tags": s.get("Tags", [])} if s.get("Tags") is not None else {})
        })

    return proxy_response(200, payload)
