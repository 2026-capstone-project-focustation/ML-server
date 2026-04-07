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

variable "app_port" {
  description = "Port exposed by the FastAPI service"
  type        = number
  default     = 8000
}

variable "allowed_ssh_cidrs" {
  description = "CIDR blocks allowed to access SSH"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "allowed_app_cidrs" {
  description = "CIDR blocks allowed to access the FastAPI app"
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
