output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "pipeline_name" {
  description = "CodePipeline name"
  value       = aws_codepipeline.main.name
}

output "reports_bucket" {
  description = "S3 bucket for reports"
  value       = aws_s3_bucket.reports.bucket
}

output "artifacts_bucket" {
  description = "S3 bucket for pipeline artifacts"
  value       = aws_s3_bucket.pipeline_artifacts.bucket
}

output "approval_topic_arn" {
  description = "SNS topic ARN for pipeline approvals"
  value       = aws_sns_topic.pipeline_approvals.arn
}

output "staging_cluster_name" {
  description = "Staging ECS cluster name"
  value       = aws_ecs_cluster.staging.name
}

output "production_cluster_name" {
  description = "Production ECS cluster name"
  value       = aws_ecs_cluster.production.name
}

output "get_instance_ips_command" {
  description = "Command to get EC2 instance public IPs"
  value       = "Run: scripts/get-instance-ips.ps1 (PowerShell) or scripts/get-instance-ips.sh (Bash)"
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.postgres.db_name
}
