# 배포 후 EC2 인스턴스를 AWS 콘솔이나 CLI에서 찾을 때 사용한다.
output "ec2_instance_id" {
  description = "ID of the EC2 instance running the application"
  value       = aws_instance.app.id
}

# 도메인 A 레코드에 연결할 고정 public IP.
output "ec2_public_ip" {
  description = "Elastic public IP address of the EC2 instance"
  value       = aws_eip.app.public_ip
}

# 인스턴스 접속 확인용 기본 SSH 명령어.
output "ssh_command" {
  description = "Base SSH command for connecting to the EC2 instance"
  value       = "ssh ec2-user@${aws_eip.app.public_ip}"
}

# TLS를 아직 붙이지 않았거나 도메인이 없을 때 확인할 HTTP 주소.
output "http_url" {
  description = "HTTP endpoint exposed by Nginx"
  value       = var.domain_name != "" ? "http://${var.domain_name}" : "http://${aws_eip.app.public_ip}"
}

# certbot TLS를 활성화한 경우 앱이 최종적으로 노출될 HTTPS 주소.
output "https_url" {
  description = "HTTPS endpoint exposed by Nginx when TLS is enabled"
  value       = var.enable_certbot_tls && var.domain_name != "" ? "https://${var.domain_name}" : null
}

# Docker 이미지 push 대상 ECR 저장소 정보.
output "ecr_repository_name" {
  description = "Name of the ECR repository for the application"
  value       = aws_ecr_repository.app.name
}

output "ecr_repository_url" {
  description = "Repository URL for pushing application images"
  value       = aws_ecr_repository.app.repository_url
}
