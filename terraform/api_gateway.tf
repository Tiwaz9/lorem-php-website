resource "aws_api_gateway_rest_api" "inventory_api" {
  name = "${var.project_name}-inventory-api"
}

resource "aws_api_gateway_resource" "inventory" {
  rest_api_id = aws_api_gateway_rest_api.inventory_api.id
  parent_id   = aws_api_gateway_rest_api.inventory_api.root_resource_id
  path_part   = "inventory"
}

resource "aws_api_gateway_method" "get_inventory" {
  rest_api_id   = aws_api_gateway_rest_api.inventory_api.id
  resource_id   = aws_api_gateway_resource.inventory.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "lambda_inventory" {
  rest_api_id             = aws_api_gateway_rest_api.inventory_api.id
  resource_id             = aws_api_gateway_resource.inventory.id
  http_method             = aws_api_gateway_method.get_inventory.http_method
  integration_http_method = "POST"
  type                    = "AWS_PROXY"
  uri                     = aws_lambda_function.InventoryVPCandSubnets.invoke_arn
}

resource "aws_lambda_permission" "apigw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.InventoryVPCandSubnets.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.inventory_api.execution_arn}/*/GET/inventory"
}

resource "aws_api_gateway_deployment" "deployment" {
  depends_on = [aws_api_gateway_integration.lambda_inventory]
  rest_api_id = aws_api_gateway_rest_api.inventory_api.id
  stage_name  = "prod"
}

output "inventory_api_url" {
  value = "https://${aws_api_gateway_rest_api.inventory_api.id}.execute-api.${var.aws_region}.amazonaws.com/${aws_api_gateway_deployment.deployment.stage_name}/inventory"
}
