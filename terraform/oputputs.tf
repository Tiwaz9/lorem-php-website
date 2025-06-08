output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer (HTTP endpoint)"
  value       = aws_lb.web_alb.dns_name
}

