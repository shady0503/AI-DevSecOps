# SNS Topic for manual approval
resource "aws_sns_topic" "pipeline_approvals" {
  name = "${var.project_name}-pipeline-approvals"

  tags = {
    Name        = "${var.project_name}-approvals"
    Environment = var.environment
  }
}

# CodePipeline
resource "aws_codepipeline" "main" {
  name     = "${var.project_name}-pipeline"
  role_arn = aws_iam_role.codepipeline.arn

  artifact_store {
    location = aws_s3_bucket.pipeline_artifacts.bucket
    type     = "S3"
  }

  # Stage 1: Source
  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "ThirdParty"
      provider         = "GitHub"
      version          = "1"
      output_artifacts = ["source_output"]

      configuration = {
        Owner      = var.github_repo_owner
        Repo       = var.github_repo_name
        Branch     = var.github_branch
        OAuthToken = var.github_token
      }
    }
  }

  # Stage 2: Build and Test
  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["build_output"]

      configuration = {
        ProjectName = aws_codebuild_project.build.name
      }
    }
  }

  # Stage 3: SAST
  stage {
    name = "SAST"

    action {
      name             = "StaticAnalysis"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["sast_output"]

      configuration = {
        ProjectName = aws_codebuild_project.sast.name
      }
    }
  }

  # Stage 4: Container Analysis
  stage {
    name = "ContainerScan"

    action {
      name             = "ContainerSecurity"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["scan_output"]

      configuration = {
        ProjectName = aws_codebuild_project.container_scan.name
      }
    }
  }

  # Stage 5: Deploy to Staging
  stage {
    name = "DeployStaging"

    action {
      name            = "DeployToStaging"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      version         = "1"
      input_artifacts = ["build_output"]

      configuration = {
        ClusterName = aws_ecs_cluster.staging.name
        ServiceName = aws_ecs_service.staging.name
        FileName    = "imagedefinitions.json"
      }
    }
  }

  # Stage 6: DAST
  stage {
    name = "DAST"

    action {
      name             = "DynamicAnalysis"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source_output"]
      output_artifacts = ["dast_output"]

      configuration = {
        ProjectName = aws_codebuild_project.dast.name
      }
    }
  }

  # Stage 7: Manual Approval
  stage {
    name = "ManualApproval"

    action {
      name     = "ApproveProduction"
      category = "Approval"
      owner    = "AWS"
      provider = "Manual"
      version  = "1"

      configuration = {
        NotificationArn = aws_sns_topic.pipeline_approvals.arn
        CustomData      = "Please review the test results and approve deployment to production"
      }
    }
  }

  # Stage 8: Deploy to Production
  stage {
    name = "DeployProduction"

    action {
      name            = "DeployToProduction"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      version         = "1"
      input_artifacts = ["build_output"]

      configuration = {
        ClusterName = aws_ecs_cluster.production.name
        ServiceName = aws_ecs_service.production.name
        FileName    = "imagedefinitions.json"
      }
    }
  }

  tags = {
    Name        = "${var.project_name}-pipeline"
    Environment = var.environment
  }
}
