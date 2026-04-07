variable "project_name" {
  description = "Name used for AWS resources"
  type        = string
  default     = "focustation-fastapi"
}

variable "aws_region" {
  description = "AWS region to deploy into"
  type        = string
  default     = "ap-northeast-2"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "key_pair_name" {
  description = "Existing AWS EC2 key pair name for SSH access"
  type        = string
}

variable "acm_certificate_arn" {
  description = "Existing ACM certificate ARN for the HTTPS listener"
  type        = string
}

variable "ecr_repository_name" {
  description = "ECR repository name for the application image"
  type        = string
  default     = "focustation-ml-server"
}

variable "container_image_uri" {
  description = "Docker image URI to run on the EC2 instance"
  type        = string
}

variable "api_key" {
  description = "API key injected into the application container"
  type        = string
  sensitive   = true
}

variable "app_port" {
  description = "Port exposed by the FastAPI container"
  type        = number
  default     = 8000
}

variable "health_check_path" {
  description = "Path used by the ALB target group health check"
  type        = string
  default     = "/health"
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to access SSH on the EC2 instance"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "allowed_http_cidrs" {
  description = "CIDR blocks allowed to access HTTP on the ALB"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "allowed_https_cidrs" {
  description = "CIDR blocks allowed to access HTTPS on the ALB"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
