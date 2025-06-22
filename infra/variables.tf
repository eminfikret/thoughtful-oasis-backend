variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "thoughtful-oasis-backend"
}

variable "aws_region" {
  default = "us-east-1"
}

variable "vpc_cidr_block" {
  description = "CIDR block for the VPC network"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_1_cidr" {
  description = "Public subnet 1 cidr block"
  default = "10.0.1.0/24"
}

variable "public_subnet_2_cidr" {
  description = "Public subnet 2 cidr block"
  default = "10.0.2.0/24"
}

variable "private_subnet_1_cidr" {
  description = "Private subnet 1 cidr block"
  default = "10.0.3.0/24"
}

variable "private_subnet_2_cidr" {
  description = "Private subnet 2 cidr block"
  default = "10.0.4.0/24"
}

variable "availability_zone_1" {
  description = "availability zone"
  default = "us-east-1a"
}

variable "availability_zone_2" {
  description = "availability zone"
  default = "us-east-1b"
}

variable "ami_id" {
  description = "The AMI ID for the EC2 instance"
  default     = "ami-04b70fa74e45c3917"
}

variable "key_name" {
  description = "The key pair name to use for the EC2 instance"
  default     = "vockey"
}

variable "instance_type" {
  description = "The type of the EC2 instance"
  default     = "t2.micro"
}

variable "ci_deploy_user" {
  description = "Username for accessing the Docker registry."
  default     = ""
}

variable "ci_deploy_password" {
  description = "Password for accessing the Docker registry."
  default     = ""
}

variable "ci_registry" {
  description = "URL of the Docker registry."
  default     = ""
}

variable "ci_registry_image" {
  description = "Name of the Docker image in the registry."
  default     = ""
}

variable "ci_commit_short_sha" {
  description = "Commit slug or tag of the Docker image."
  default     = "latest"
}

variable "db_name" {
  default = "factcheckdb"
}

variable "db_user" {
  default = "postgres"
}

variable "db_password" {
  default = ""
}

variable "node_env" {
  description = "The NODE_ENV value (e.g., test or production)"
  type        = string
  default     = ""
}