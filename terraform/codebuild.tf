# CodeBuild project for Build and Test
resource "aws_codebuild_project" "build" {
  name          = "${var.project_name}-build"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 30

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/standard:7.0"
    type                       = "LINUX_CONTAINER"
    privileged_mode            = true
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = aws_ecr_repository.app.name
    }

    environment_variable {
      name  = "REPORTS_BUCKET"
      value = aws_s3_bucket.reports.id
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-build.yml"
  }

  tags = {
    Name        = "${var.project_name}-build"
    Environment = var.environment
  }
}

# CodeBuild project for SAST
resource "aws_codebuild_project" "sast" {
  name          = "${var.project_name}-sast"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 20

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/standard:7.0"
    type                       = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "REPORTS_BUCKET"
      value = aws_s3_bucket.reports.id
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-sast.yml"
  }

  tags = {
    Name        = "${var.project_name}-sast"
    Environment = var.environment
  }
}

# CodeBuild project for Container Scan
resource "aws_codebuild_project" "container_scan" {
  name          = "${var.project_name}-container-scan"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 20

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/standard:7.0"
    type                       = "LINUX_CONTAINER"
    privileged_mode            = true
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.account_id
    }

    environment_variable {
      name  = "AWS_DEFAULT_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "IMAGE_REPO_NAME"
      value = aws_ecr_repository.app.name
    }

    environment_variable {
      name  = "REPORTS_BUCKET"
      value = aws_s3_bucket.reports.id
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-container-scan.yml"
  }

  tags = {
    Name        = "${var.project_name}-container-scan"
    Environment = var.environment
  }
}

# CodeBuild project for Secrets Scanning (Gitleaks)
resource "aws_codebuild_project" "gitleaks" {
  name          = "${var.project_name}-gitleaks"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 15

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/standard:7.0"
    type                       = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "REPORTS_BUCKET"
      value = aws_s3_bucket.reports.id
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-gitleaks.yml"
  }

  tags = {
    Name        = "${var.project_name}-gitleaks"
    Environment = var.environment
  }
}

# CodeBuild project for Code Quality Analysis (SpotBugs + OWASP Dependency-Check)
resource "aws_codebuild_project" "sonarqube" {
  name          = "${var.project_name}-code-quality"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 30

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/standard:7.0"
    type                       = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "REPORTS_BUCKET"
      value = aws_s3_bucket.reports.id
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-sonarqube.yml"
  }

  tags = {
    Name        = "${var.project_name}-code-quality"
    Environment = var.environment
  }
}

# CodeBuild project for IaC Security (Checkov)
resource "aws_codebuild_project" "checkov" {
  name          = "${var.project_name}-checkov"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 15

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/standard:7.0"
    type                       = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "REPORTS_BUCKET"
      value = aws_s3_bucket.reports.id
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-checkov.yml"
  }

  tags = {
    Name        = "${var.project_name}-checkov"
    Environment = var.environment
  }
}

# CodeBuild project for DAST (Enhanced)
resource "aws_codebuild_project" "dast" {
  name          = "${var.project_name}-dast"
  service_role  = aws_iam_role.codebuild.arn
  build_timeout = 60  # Increased for full scan

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type                = "BUILD_GENERAL1_SMALL"
    image                      = "aws/codebuild/standard:7.0"
    type                       = "LINUX_CONTAINER"
    image_pull_credentials_type = "CODEBUILD"

    environment_variable {
      name  = "STAGING_URL"
      value = var.staging_url
    }

    environment_variable {
      name  = "REPORTS_BUCKET"
      value = aws_s3_bucket.reports.id
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec-dast.yml"
  }

  tags = {
    Name        = "${var.project_name}-dast"
    Environment = var.environment
  }
}
