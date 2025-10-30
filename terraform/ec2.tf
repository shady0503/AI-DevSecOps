# Get latest ECS-optimized AMI
data "aws_ami" "ecs_optimized" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-ecs-hvm-*-x86_64-ebs"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# Launch Template for Staging
resource "aws_launch_template" "ecs_staging" {
  name_prefix   = "${var.project_name}-staging-"
  image_id      = data.aws_ami.ecs_optimized.id
  instance_type = "t2.micro"  # FREE TIER!

  iam_instance_profile {
    name = aws_iam_instance_profile.ecs.name
  }

  vpc_security_group_ids = [aws_security_group.ecs.id]

  user_data = base64encode(<<-EOF
              #!/bin/bash
              echo ECS_CLUSTER=${aws_ecs_cluster.staging.name} >> /etc/ecs/ecs.config
              EOF
  )

  monitoring {
    enabled = false  # Detailed monitoring costs extra
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-staging-ecs-instance"
    }
  }
}

# Auto Scaling Group for Staging
resource "aws_autoscaling_group" "ecs_staging" {
  name                = "${var.project_name}-staging-asg"
  vpc_zone_identifier = aws_subnet.public[*].id
  min_size            = 1
  max_size            = 1  # Keep at 1 for free tier
  desired_capacity    = 1

  launch_template {
    id      = aws_launch_template.ecs_staging.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-staging-ecs"
    propagate_at_launch = true
  }

  tag {
    key                 = "AmazonECSManaged"
    value               = true
    propagate_at_launch = true
  }
}

# Launch Template for Production
resource "aws_launch_template" "ecs_production" {
  name_prefix   = "${var.project_name}-prod-"
  image_id      = data.aws_ami.ecs_optimized.id
  instance_type = "t2.micro"  # FREE TIER!

  iam_instance_profile {
    name = aws_iam_instance_profile.ecs.name
  }

  vpc_security_group_ids = [aws_security_group.ecs.id]

  user_data = base64encode(<<-EOF
              #!/bin/bash
              echo ECS_CLUSTER=${aws_ecs_cluster.production.name} >> /etc/ecs/ecs.config
              EOF
  )

  monitoring {
    enabled = false  # Detailed monitoring costs extra
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name = "${var.project_name}-production-ecs-instance"
    }
  }
}

# Auto Scaling Group for Production
resource "aws_autoscaling_group" "ecs_production" {
  name                = "${var.project_name}-prod-asg"
  vpc_zone_identifier = aws_subnet.public[*].id
  min_size            = 1
  max_size            = 1  # Keep at 1 for free tier
  desired_capacity    = 1

  launch_template {
    id      = aws_launch_template.ecs_production.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.project_name}-production-ecs"
    propagate_at_launch = true
  }

  tag {
    key                 = "AmazonECSManaged"
    value               = true
    propagate_at_launch = true
  }
}

# Capacity Provider for Staging
resource "aws_ecs_capacity_provider" "staging" {
  name = "${var.project_name}-staging-capacity-provider"

  auto_scaling_group_provider {
    auto_scaling_group_arn         = aws_autoscaling_group.ecs_staging.arn
    managed_termination_protection = "DISABLED"

    managed_scaling {
      status          = "ENABLED"
      target_capacity = 100
    }
  }
}

# Capacity Provider for Production
resource "aws_ecs_capacity_provider" "production" {
  name = "${var.project_name}-prod-capacity-provider"

  auto_scaling_group_provider {
    auto_scaling_group_arn         = aws_autoscaling_group.ecs_production.arn
    managed_termination_protection = "DISABLED"

    managed_scaling {
      status          = "ENABLED"
      target_capacity = 100
    }
  }
}

# Associate Capacity Providers with Clusters
resource "aws_ecs_cluster_capacity_providers" "staging" {
  cluster_name = aws_ecs_cluster.staging.name

  capacity_providers = [aws_ecs_capacity_provider.staging.name]

  default_capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.staging.name
    weight            = 1
    base              = 1
  }
}

resource "aws_ecs_cluster_capacity_providers" "production" {
  cluster_name = aws_ecs_cluster.production.name

  capacity_providers = [aws_ecs_capacity_provider.production.name]

  default_capacity_provider_strategy {
    capacity_provider = aws_ecs_capacity_provider.production.name
    weight            = 1
    base              = 1
  }
}
