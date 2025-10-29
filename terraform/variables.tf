variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "eu-west-3"  # Paris region
}

variable "project_name" {
  description = "Project name"
  type        = string
  default     = "social-media-api"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "dev"
}

variable "github_repo_owner" {
  description = "GitHub repository owner"
  type        = string
  default     = "shady0503"
}

variable "github_repo_name" {
  description = "GitHub repository name"
  type        = string
  default     = "Sample"
}

variable "github_branch" {
  description = "GitHub branch to trigger pipeline"
  type        = string
  default     = "master"
}

variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
}

variable "staging_url" {
  description = "Staging environment URL for DAST testing (use EC2 instance IP after deployment)"
  type        = string
  default     = "http://REPLACE_WITH_EC2_IP:8080"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "postgres"
}

variable "db_password" {
  description = "Database master password"
  type        = string
  sensitive   = true
  default     = "ChangeMe123!"  # Change this in terraform.tfvars
}
