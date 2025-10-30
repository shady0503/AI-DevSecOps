output "ecr_repository_url" {
  description = "ECR repository URL"
  value       = aws_ecr_repository.app.repository_url
}

output "staging_cluster_name" {
  description = "Staging ECS cluster name"
  value       = aws_ecs_cluster.staging.name
}

output "production_cluster_name" {
  description = "Production ECS cluster name"
  value       = aws_ecs_cluster.production.name
}

output "rds_endpoint" {
  description = "RDS PostgreSQL endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.postgres.db_name
}

output "staging_instance_ip_command" {
  description = "Command to get staging instance IP"
  value       = "aws ec2 describe-instances --filters 'Name=tag:Name,Values=${var.project_name}-staging-ecs-instance' 'Name=instance-state-name,Values=running' --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --region ${var.aws_region}"
}

output "production_instance_ip_command" {
  description = "Command to get production instance IP"
  value       = "aws ec2 describe-instances --filters 'Name=tag:Name,Values=${var.project_name}-production-ecs-instance' 'Name=instance-state-name,Values=running' --query 'Reservations[0].Instances[0].PublicIpAddress' --output text --region ${var.aws_region}"
}
