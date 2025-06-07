import json
import os
from datetime import datetime, timezone
import boto3
from botocore.exceptions import ClientError

# DynamoDB table name (if you still want to write to it)
DDB_TABLE_NAME = os.environ.get("DDB_TABLE_NAME", "NetworkInventory")

# AWS EC2 client
ec2 = boto3.client("ec2")

def iso_timestamp_now():
    """Return current UTC time as an ISO-formatted string."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def proxy_response(status_code, body_obj):
    """Helper to build an AWS_PROXY–compatible response with CORS."""
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
    2) (Optional) Write inventory to DynamoDB
    3) Return full details of resources in JSON
    """
    timestamp = iso_timestamp_now()

    # Fetch VPCs
    try:
        vpcs = ec2.describe_vpcs().get("Vpcs", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeVpcs failed: {e}"})

    # Fetch Subnets
    try:
        subnets = ec2.describe_subnets().get("Subnets", [])
    except ClientError as e:
        return proxy_response(500, {"error": f"DescribeSubnets failed: {e}"})

    # Optional: DynamoDB write (uncomment if needed)
    # from your_module import build_and_batch_write
    # try:
    #     build_and_batch_write(DDB_TABLE_NAME, vpcs, subnets, timestamp)
    # except Exception as e:
    #     print(f"DynamoDB write failed: {e}")

    # Build the JSON payload with detailed fields
    payload = {
        "timestamp":   timestamp,
        "vpcCount":    len(vpcs),
        "subnetCount": len(subnets),
        "vpcs":        [
            {
                "VpcId":             v.get("VpcId"),
                "CidrBlock":         v.get("CidrBlock"),
                "State":             v.get("State"),
                "IsDefault":         v.get("IsDefault"),
                "Tags":              v.get("Tags", [])
            } for v in vpcs
        ],
        "subnets":     [
            {
                "SubnetId":               s.get("SubnetId"),
                "VpcId":                  s.get("VpcId"),
                "CidrBlock":              s.get("CidrBlock"),
                "AvailabilityZone":       s.get("AvailabilityZone"),
                "State":                  s.get("State"),
                "AvailableIpAddressCount": s.get("AvailableIpAddressCount"),
                "DefaultForAz":           s.get("DefaultForAz"),
                "MapPublicIpOnLaunch":    s.get("MapPublicIpOnLaunch"),
                "Tags":                   s.get("Tags", [])
            } for s in subnets
        ]
    }

    return proxy_response(200, payload)
