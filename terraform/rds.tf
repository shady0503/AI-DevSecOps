# RDS PostgreSQL Database (Free Tier)

# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.project_name}-db-subnet-group"
  subnet_ids = aws_subnet.public[*].id

  tags = {
    Name = "${var.project_name}-db-subnet-group"
  }
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  vpc_id      = aws_vpc.main.id
  description = "Security group for RDS PostgreSQL"

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
    description     = "Allow PostgreSQL from ECS instances"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

# RDS PostgreSQL Instance (Free Tier)
resource "aws_db_instance" "postgres" {
  identifier        = "${var.project_name}-db"
  engine            = "postgres"
  engine_version    = "15.14"  # Latest available in eu-west-3
  instance_class    = "db.t3.micro"  # FREE TIER: 750 hours/month
  allocated_storage = 20              # FREE TIER: 20GB

  db_name  = "social_media_db"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  publicly_accessible    = false

  # Free tier optimizations
  storage_type          = "gp2"
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "mon:04:00-mon:05:00"
  
  skip_final_snapshot       = true  # Change to false for production
  final_snapshot_identifier = "${var.project_name}-final-snapshot"
  
  # Disable features that cost extra
  enabled_cloudwatch_logs_exports = []
  performance_insights_enabled    = false
  monitoring_interval             = 0
  
  # Free tier eligible options
  multi_az               = false  # Single AZ for free tier
  deletion_protection    = false  # Set to true for production
  storage_encrypted      = true

  tags = {
    Name        = "${var.project_name}-postgres"
    Environment = var.environment
  }
}
