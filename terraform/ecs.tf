# VPC for ECS
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "${var.project_name}-vpc"
  }
}

resource "aws_subnet" "public" {
  count                   = 2
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true

  tags = {
    Name = "${var.project_name}-public-${count.index + 1}"
  }
}

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "${var.project_name}-igw"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "${var.project_name}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count          = 2
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

# Security Group for EC2 instances - Direct access without ALB
resource "aws_security_group" "ecs" {
  name        = "${var.project_name}-ecs-sg"
  vpc_id      = aws_vpc.main.id
  description = "Security group for ECS EC2 instances"

  # Allow direct access to application port
  ingress {
    from_port   = 8080
    to_port     = 8080
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow HTTP traffic to application"
  }

  # Allow SSH for troubleshooting (restrict in production)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
    description = "Allow SSH access"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project_name}-ecs-sg"
  }
}

# ECS Clusters
resource "aws_ecs_cluster" "staging" {
  name = "${var.project_name}-staging"

  setting {
    name  = "containerInsights"
    value = "disabled"  # Disabled to save costs
  }

  tags = {
    Name        = "${var.project_name}-staging"
    Environment = "staging"
  }
}

resource "aws_ecs_cluster" "production" {
  name = "${var.project_name}-production"

  setting {
    name  = "containerInsights"
    value = "disabled"  # Disabled to save costs
  }

  tags = {
    Name        = "${var.project_name}-production"
    Environment = "production"
  }
}

# Task Definition for EC2
resource "aws_ecs_task_definition" "app" {
  family                = var.project_name
  network_mode          = "bridge"  # EC2 mode
  task_role_arn         = aws_iam_role.ecs_task_execution.arn
  execution_role_arn    = aws_iam_role.ecs_task_execution.arn

  container_definitions = jsonencode([{
    name      = "social-media-app"
    image     = "${aws_ecr_repository.app.repository_url}:latest"
    memory    = 400  # Leave some memory for system
    essential = true
    
    portMappings = [{
      containerPort = 8080
      hostPort      = 8080
      protocol      = "tcp"
    }]

    environment = [
      {
        name  = "SPRING_DATASOURCE_URL"
        value = "jdbc:postgresql://${aws_db_instance.postgres.address}:5432/social_media_db"
      },
      {
        name  = "SPRING_DATASOURCE_USERNAME"
        value = var.db_username
      },
      {
        name  = "SPRING_DATASOURCE_PASSWORD"
        value = var.db_password
      },
      {
        name  = "SPRING_JPA_HIBERNATE_DDL_AUTO"
        value = "update"
      }
    ]

    logConfiguration = {
      logDriver = "awslogs"
      options = {
        "awslogs-group"         = "/ecs/${var.project_name}"
        "awslogs-region"        = var.aws_region
        "awslogs-stream-prefix" = "ecs"
      }
    }
  }])
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.project_name}"
  retention_in_days = 1  # Minimum retention for free tier
}

# ECS Service - Staging (No ALB - Direct EC2 access)
resource "aws_ecs_service" "staging" {
  name            = "${var.project_name}-staging-service"
  cluster         = aws_ecs_cluster.staging.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "EC2"

  # Deployment configuration for single EC2 instance with static ports
  deployment_minimum_healthy_percent = 0    # Allow stopping old task before starting new one
  deployment_maximum_percent         = 100  # Only run 1 task at a time

  # Force new deployment on each update
  force_new_deployment = true

  depends_on = [
    aws_autoscaling_group.ecs_staging
  ]
}

# ECS Service - Production (No ALB - Direct EC2 access)
resource "aws_ecs_service" "production" {
  name            = "${var.project_name}-prod-service"
  cluster         = aws_ecs_cluster.production.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "EC2"

  # Deployment configuration for single EC2 instance with static ports
  deployment_minimum_healthy_percent = 0    # Allow stopping old task before starting new one
  deployment_maximum_percent         = 100  # Only run 1 task at a time

  # Force new deployment on each update
  force_new_deployment = true

  depends_on = [
    aws_autoscaling_group.ecs_production
  ]
}
