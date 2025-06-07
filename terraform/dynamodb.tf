# terraform/dynamodb.tf

# DynamoDB table for storing VPC and Subnet inventory
resource "aws_dynamodb_table" "network_inventory" {
  name           = var.ddb_table_name
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "PK"
  range_key      = "SK"

  attribute {
    name = "PK"
    type = "S"
  }

  attribute {
    name = "SK"
    type = "S"
  }

  tags = {
    Name = "${var.project_name}-network-inventory"
  }
}
