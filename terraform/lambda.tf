
# 1) Zip up your Python handler from ../lambda folder
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../lambda/lambda_inventory.py"
  output_path = "${path.module}/lambda_inventory.zip"
}

# 2) IAM Role for Lambda execution
data "aws_iam_policy_document" "lambda_assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda_exec" {
  name               = "${var.project_name}-lambda-exec"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume.json
}

# 3) Attach managed policies
resource "aws_iam_role_policy_attachment" "basic_exec" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}
resource "aws_iam_role_policy_attachment" "ec2_read" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ReadOnlyAccess"
}
resource "aws_iam_role_policy_attachment" "ddb_full" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess"
}

# 4) Create the Lambda function in eu-west-2
resource "aws_lambda_function" "inventory" {
  function_name = var.lambda_function_name
  filename      = data.archive_file.lambda_zip.output_path
  handler       = "lambda_inventory.lambda_handler"
  runtime       = "python3.9"
  role          = aws_iam_role.lambda_exec.arn

  environment {
    variables = {
      DDB_TABLE_NAME = var.ddb_table_name
    }
  }

  # ensure the IAM attachments are created first
depends_on = [
  aws_iam_role_policy_attachment.basic_exec,
  aws_iam_role_policy_attachment.ec2_read,
  aws_iam_role_policy_attachment.ddb_full,
]
}

# 5) Output the Lambda ARN for API Gateway integration
output "inventory_lambda_arn" {
  description = "ARN of the deployed Inventory Lambda"
  value       = aws_lambda_function.inventory.arn
}
