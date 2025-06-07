import json
import os
from datetime import datetime, timezone
import time

import boto3
from botocore.exceptions import ClientError

# DynamoDB table name (optional)
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
    Describes all VPCs and Subnets, writes to DynamoDB, and returns full resource details.
    """
    timestamp = iso_timestamp_now()

    # Describe VPCs
    try:
        vpcs_resp = ec2.describe_vpcs()
        vpcs = vpcs_resp.get("Vpcs", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeVpcs failed: {str(e)}"})

    # Describe Subnets
    try:
        subnets_resp = ec2.describe_subnets()
        subnets = subnets_resp.get("Subnets", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeSubnets failed: {str(e)}"})

    # Optional: write inventory to DynamoDB
    # items = []
    # for v in vpcs:
    #     items.append({"VPC": v})
    # for s in subnets:
    #     items.append({"Subnet": s})
    # batch_write(DDB_TABLE_NAME, items)

    # Build detailed payload
    payload = {
        "timestamp":   timestamp,
        "vpcCount":    len(vpcs),
        "subnetCount": len(subnets),
        "vpcs":        vpcs,
        "subnets":     subnets
    }

    return proxy_response(200, payload)
