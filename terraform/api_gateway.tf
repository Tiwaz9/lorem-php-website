# terraform/api_gateway.tf

# 1) REST API for inventory
resource "aws_api_gateway_rest_api" "inventory_api" {
  name = "${var.project_name}-inventory-api"
}

# 2) /inventory resource
resource "aws_api_gateway_resource" "inventory" {
  rest_api_id = aws_api_gateway_rest_api.inventory_api.id
  parent_id   = aws_api_gateway_rest_api.inventory_api.root_resource_id
  path_part   = "inventory"
}

# 3) GET /inventory method
resource "aws_api_gateway_method" "get_inventory" {
  rest_api_id   = aws_api_gateway_rest_api.inventory_api.id
  resource_id   = aws_api_gateway_resource.inventory.id
  http_method   = "GET"
  authorization = "NONE"
}

# 4) Integration with your Lambda (AWS_PROXY)
resource "aws_api_gateway_integration" "lambda_inventory" {
  rest_api_id             = aws_api_gateway_rest_api.inventory_api.id
  resource_id             = aws_api_gateway_resource.inventory.id
  http_method             = aws_api_gateway_method.get_inventory.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"

  # Reference the aws_lambda_function.inventory resource's ARN
  uri = "arn:aws:apigateway:${var.aws_region}:lambda:path/2015-03-31/functions/${aws_lambda_function.inventory.arn}/invocations"
}

# 5) Permission for API Gateway to invoke the Lambda
resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  # Reference the Lambda resource's function name
  function_name = aws_lambda_function.inventory.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.inventory_api.execution_arn}/*/GET/inventory"
}

# 6) Deployment to prod stage
resource "aws_api_gateway_deployment" "deployment" {
  depends_on  = [aws_api_gateway_integration.lambda_inventory]
  rest_api_id = aws_api_gateway_rest_api.inventory_api.id
  stage_name  = "prod"
}

# 7) Output the full invoke URL
output "inventory_api_url" {
  description = "Invoke URL for GET /inventory"
  value       = "https://${aws_api_gateway_rest_api.inventory_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_deployment.deployment.stage_name}/inventory"
}
