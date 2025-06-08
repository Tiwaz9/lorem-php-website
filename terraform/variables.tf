variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-west-2"
}

variable "project_name" {
  description = "Project name used as a prefix for all resources"
  type        = string
  default     = "lorem"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnets" {
  description = "List of CIDRs for public subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnets" {
  description = "List of CIDRs for private subnets (one per AZ)"
  type        = list(string)
  default     = ["10.0.101.0/24", "10.0.102.0/24"]
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "desired_capacity" {
  description = "Desired number of instances in the Auto Scaling Group"
  type        = number
  default     = 1
}

variable "max_size" {
  description = "Maximum number of instances in the ASG"
  type        = number
  default     = 2
}

variable "min_size" {
  description = "Minimum number of instances in the ASG"
  type        = number
  default     = 1
}

variable "github_repo_url" {
  description = "HTTPS URL of the public GitHub repository containing the PHP code"
  type        = string
  default     = "https://github.com/Tiwaz9/lorem-php-website.git"
}

variable "github_repo_branch" {
  description = "Branch or tag to checkout from the GitHub repo (e.g. main or master)"
  type        = string
  default     = "main"
}
variable "lambda_function_name" {
  description = "Name of your Lambda function"
  type        = string
  default     = "InventoryVPCandSubnets"
}

variable "lambda_function_arn" {
  description = "ARN of your Lambda function"
  type        = string
  default     = "arn:aws:lambda:eu-west-2:976193219226:function:InventoryVPCandSubnets"
}

variable "ddb_table_name" {
  default = "NetworkInventory"
}