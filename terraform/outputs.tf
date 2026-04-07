output "alb_dns_name" {
  description = "DNS name of the application load balancer"
  value       = aws_lb.app.dns_name
}

output "https_url" {
  description = "HTTPS endpoint exposed by the load balancer"
  value       = "https://${aws_lb.app.dns_name}"
}

output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.app.public_ip
}
