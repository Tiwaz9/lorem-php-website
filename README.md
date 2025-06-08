Lorem PHP Website & Infrastructure

This project demonstrates a simple PHP application hosted on AWS with a professional DevOps infrastructure managed by Terraform. It includes:

A PHP website serving Lorem Ipsum text and an image behind an Application Load Balancer (ALB) & Auto Scaling Group (ASG) in a VPC.

An AWS Lambda function that inventories all VPCs and Subnets in the account, persists them to DynamoDB, and exposes them via API Gateway.

Infrastructure as Code (Terraform) to provision all required AWS resources: VPC, subnets, NAT, routing, security groups, ALB, ASG, Lambda, API Gateway, DynamoDB, IAM roles, etc.

Repository Structure

Lorem/
├── app/
│   └── public/
│       ├── index.php      # Main PHP page & JavaScript UI
│       └── image.png      # Sample image
├── lambda/
│   └── lambda_inventory.py  # Python handler for inventory Lambda
├── terraform/
│   ├── providers.tf      # Terraform provider configuration
│   ├── variables.tf      # Input variables and defaults
│   ├── vpc.tf            # VPC, subnets, NAT, route tables
│   ├── security_groups.tf# Security groups for ALB & EC2
│   ├── iam.tf            # IAM roles & policies for Lambda and EC2
│   ├── alb_asg.tf        # ALB, target group, listener, ASG & launch template
│   ├── api_gateway.tf    # API Gateway REST API + integration & permissions
│   ├── lambda.tf         # Lambda function deployment and archive
│   ├── dynamodb.tf       # DynamoDB table definition
│   └── outputs.tf        # Terraform outputs (e.g. ALB DNS, API URL)
└── README.md             # This file

Prerequisites

AWS CLI configured with credentials for your account

Terraform >= 1.0 installed

Git for cloning and pushing the repo

Getting Started

Clone the repository

git clone https://github.com/Tiwaz9/lorem-php-website.git
cd lorem-php-website

Configure variables (optional)

In terraform/variables.tf, you can override defaults for things like region, instance sizes, CIDR blocks, GitHub repo URL, etc.

You may also export environment variables:

export TF_VAR_aws_region=eu-west-2
export TF_VAR_project_name=lorem

Deploy Infrastructure & Application
The Terraform configuration will:

Create a VPC with public and private subnets

Deploy an Application Load Balancer (ALB) in public subnets

Launch EC2 instances in private subnets via an Auto Scaling Group (ASG)

Install NGINX + PHP-FPM on EC2 instances, clone the app/public folder, and configure the site

Provision a DynamoDB table and an AWS Lambda function to inventory network resources

Create an API Gateway endpoint to invoke the Lambda

Inject the API URL into the EC2 User Data via NGINX fastcgi_param

cd terraform
terraform init
terraform apply -auto-approve

View the Application

ALB DNS: Run terraform output alb_dns_name to get the ALB URL and open it in your browser.

API URL: Run terraform output inventory_api_url to see the GET /inventory endpoint for the Lambda.

Test the Inventory Feature

On the web page, click Fetch VPC & Subnets Inventory to see a table of all VPCs and subnets in your AWS account.

Cleaning Up

To avoid incurring charges, destroy all resources when you’re done:

cd terraform
terraform destroy -auto-approve

Notes & Considerations

Security: All EC2 instances run in private subnets; the ALB handles inbound HTTP. The Lambda has EC2 read-only and DynamoDB full-access via its IAM role.

Scalability: The ASG and ALB allow horizontal scaling. DynamoDB on-demand mode scales automatically for reads/writes.

Extensibility: You can extend the PHP app, add SSL via ACM, or integrate CI/CD pipelines for automated deployments.



