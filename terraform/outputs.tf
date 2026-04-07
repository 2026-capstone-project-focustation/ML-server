output "public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = aws_instance.fastapi_server.public_ip
}

output "app_url" {
  description = "HTTP URL for the FastAPI service"
  value       = "http://${aws_instance.fastapi_server.public_dns}:${var.app_port}"
}
