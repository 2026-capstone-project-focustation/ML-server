output "alb_dns_name" {
  description = "DNS name of the application load balancer"
  value       = aws_lb.app.dns_name
}

output "ecr_repository_name" {
  description = "Name of the ECR repository for the application"
  value       = aws_ecr_repository.app.name
}

output "ecr_repository_url" {
  description = "Repository URL for pushing application images"
  value       = aws_ecr_repository.app.repository_url
}

output "https_url" {
  description = "HTTPS endpoint exposed by the load balancer"
  value       = "https://${aws_lb.app.dns_name}"
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.app.public_ip
}
