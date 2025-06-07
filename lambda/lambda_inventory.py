
import json
import os
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

# DynamoDB table name (optional, if writing)
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
    2) Optionally persist to DynamoDB
    3) Return full details of resources in JSON
    """
    timestamp = iso_timestamp_now()

    # Describe VPCs
    try:
        vpcs_data = ec2.describe_vpcs()
        vpcs = vpcs_data.get("Vpcs", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeVpcs failed: {str(e)}"})

    # Describe Subnets
    try:
        subs_data = ec2.describe_subnets()
        subnets = subs_data.get("Subnets", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeSubnets failed: {str(e)}"})

    # Optional: persist to DynamoDB (commented out)
    # try:
    #     write_inventory_to_dynamodb(DDB_TABLE_NAME, vpcs, subnets, timestamp)
    # except Exception as e:
    #     print(f"DynamoDB write failed: {e}")

    # Build detailed payload lists
    detailed_vpcs = []
    for v in vpcs:
        detailed_vpcs.append({
            "VpcId": v.get("VpcId"),
            "CidrBlock": v.get("CidrBlock"),
            "IsDefault": v.get("IsDefault"),
            "Tags": v.get("Tags", [])
        })

    detailed_subnets = []
    for s in subnets:
        detailed_subnets.append({
            "SubnetId": s.get("SubnetId"),
            "VpcId": s.get("VpcId"),
            "CidrBlock": s.get("CidrBlock"),
            "AvailabilityZone": s.get("AvailabilityZone"),
            "MapPublicIpOnLaunch": s.get("MapPublicIpOnLaunch"),
            "Tags": s.get("Tags", [])
        })

    # Construct the response payload
    payload = {
        "timestamp":   timestamp,
        "vpcCount":    len(detailed_vpcs),
        "subnetCount": len(detailed_subnets),
        "vpcs":        detailed_vpcs,
        "subnets":     detailed_subnets
    }

    return proxy_response(200, payload)

