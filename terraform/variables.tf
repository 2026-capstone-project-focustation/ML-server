# 리소스 이름과 태그에 공통으로 사용할 프로젝트 이름.
variable "project_name" {
  description = "Name used for AWS resources"
  type        = string
  default     = "focustation-ml-server"
}

# 현재는 서울 리전을 기본값으로 사용한다.
variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-northeast-2"
}

# 계정 기본 VPC에 의존하지 않도록 앱 전용 VPC를 생성한다.
variable "vpc_cidr_block" {
  description = "CIDR block for the application VPC"
  type        = string
  default     = "10.42.0.0/16"
}

# 단일 EC2를 올릴 퍼블릭 서브넷 대역.
variable "public_subnet_cidr_block" {
  description = "CIDR block for the public subnet"
  type        = string
  default     = "10.42.1.0/24"
}

# 초기 비용을 낮게 유지하기 위한 작은 인스턴스 타입.
variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

# SSH 접속에 사용할 기존 EC2 Key Pair 이름.
variable "key_pair_name" {
  description = "Existing AWS EC2 key pair name for SSH access"
  type        = string
}

# Docker 이미지와 로그를 감안한 EC2 루트 볼륨 크기.
variable "root_volume_size_gb" {
  description = "Root EBS volume size in GiB"
  type        = number
  default     = 20
}

# CI/CD에서 빌드한 앱 이미지를 push 할 ECR 저장소 이름.
variable "ecr_repository_name" {
  description = "ECR repository name for the application image"
  type        = string
  default     = "focustation-ml-server"
}

# EC2가 부팅 시 pull 해서 실행할 Docker 이미지 URI.
# 이번 브랜치에서는 수동 배포를 기본으로 하므로 비워두면 EC2 준비만 수행한다.
variable "container_image_uri" {
  description = "Docker image URI to run on the EC2 instance"
  type        = string
  default     = ""
}

# FastAPI /score 요청에서 검증할 API Key.
# Terraform state에 남을 수 있으므로 실제 운영에서는 state 접근 권한을 제한해야 한다.
variable "api_key" {
  description = "API key injected into the application container"
  type        = string
  sensitive   = true
}

# 컨테이너 내부 FastAPI 포트. 외부에는 직접 노출하지 않는다.
variable "app_port" {
  description = "Port exposed by the FastAPI container inside the EC2 host"
  type        = number
  default     = 8000
}

# EC2 부팅 후 컨테이너가 정상 기동했는지 확인할 경로.
variable "health_check_path" {
  description = "Path used by local health checks"
  type        = string
  default     = "/health"
}

# HTTPS를 적용할 도메인 또는 서브도메인. 비워두면 IP 기반 HTTP만 구성된다.
variable "domain_name" {
  description = "Domain or subdomain for Nginx server_name and optional Let's Encrypt TLS"
  type        = string
  default     = ""
}

# Let's Encrypt 인증서 발급에 사용할 이메일.
variable "certbot_email" {
  description = "Email used for Let's Encrypt registration when TLS is enabled"
  type        = string
  default     = ""
}

# true이면 user_data에서 certbot으로 TLS 인증서 발급과 HTTP->HTTPS 리다이렉트를 구성한다.
variable "enable_certbot_tls" {
  description = "Whether user_data should request and install a Let's Encrypt certificate"
  type        = bool
  default     = false
}

# Nginx 레벨에서 클라이언트 IP별 요청 속도를 제한한다.
variable "nginx_rate_limit" {
  description = "Nginx request rate limit applied per client IP"
  type        = string
  default     = "10r/s"
}

# 순간적으로 허용할 초과 요청량. 모바일 앱의 짧은 burst를 흡수하기 위한 값이다.
variable "nginx_rate_burst" {
  description = "Nginx burst size for rate-limited requests"
  type        = number
  default     = 20
}

# SSH 허용 대역. 운영 전에는 반드시 본인 IP 대역으로 좁히는 것이 좋다.
variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to access SSH on the EC2 instance"
  type        = list(string)

  validation {
    condition     = length(var.allowed_ssh_cidrs) > 0 && alltrue([for cidr in var.allowed_ssh_cidrs : cidr != "0.0.0.0/0"])
    error_message = "allowed_ssh_cidrs must include at least one trusted CIDR and must not contain 0.0.0.0/0."
  }
}

# HTTP 접근 허용 대역. certbot 인증서 발급을 위해 80 포트가 필요하다.
variable "allowed_http_cidrs" {
  description = "CIDR blocks allowed to access HTTP on the EC2 instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

# HTTPS 접근 허용 대역.
variable "allowed_https_cidrs" {
  description = "CIDR blocks allowed to access HTTPS on the EC2 instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
