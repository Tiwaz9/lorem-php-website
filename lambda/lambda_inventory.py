import json
import os
from datetime import datetime, timezone
import time

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
    """Convert AWS tags into DynamoDB-friendly format."""
    if not tag_list:
        return []
    return [{"Key": t.get("Key", ""), "Value": t.get("Value", "")} for t in tag_list]


def proxy_response(status_code, body_obj):
    """Helper to build an AWS_PROXY-compatible response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body_obj)
    }


def lambda_handler(event, context):
    
    timestamp = iso_timestamp_now()

    # Describe VPCs
    try:
        vpcs = ec2.describe_vpcs().get("Vpcs", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeVpcs failed: {str(e)}"})

    # Describe Subnets
    try:
        subnets = ec2.describe_subnets().get("Subnets", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeSubnets failed: {str(e)}"})

  

    # Build response payload
    payload = {
        "timestamp":   timestamp,
        "vpcCount":    len(vpcs),
        "subnetCount": len(subnets),
        "vpcs":        [
            {
                "VpcId": v.get("VpcId"),
                "CidrBlock": v.get("CidrBlock"),
                "IsDefault": v.get("IsDefault"),
                "Tags": format_tags(v.get("Tags", []))
            }
            for v in vpcs
        ],
        "subnets":     [
            {
                "SubnetId": s.get("SubnetId"),
                "VpcId": s.get("VpcId"),
                "CidrBlock": s.get("CidrBlock"),
                "AvailabilityZone": s.get("AvailabilityZone"),
                "MapPublicIpOnLaunch": s.get("MapPublicIpOnLaunch"),
                "Tags": format_tags(s.get("Tags", []))
            }
            for s in subnets
        ]
    }

    return proxy_response(200, payload)

