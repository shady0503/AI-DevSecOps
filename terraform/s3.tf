# S3 bucket for pipeline artifacts
resource "aws_s3_bucket" "pipeline_artifacts" {
  bucket = "${var.project_name}-pipeline-artifacts-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.project_name}-pipeline-artifacts"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "pipeline_artifacts" {
  bucket = aws_s3_bucket.pipeline_artifacts.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 bucket for security and test reports
resource "aws_s3_bucket" "reports" {
  bucket = "${var.project_name}-reports-${data.aws_caller_identity.current.account_id}"

  tags = {
    Name        = "${var.project_name}-reports"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_versioning" "reports" {
  bucket = aws_s3_bucket.reports.id
  
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "reports" {
  bucket = aws_s3_bucket.reports.id

  rule {
    id     = "delete-old-reports"
    status = "Enabled"

    expiration {
      days = 30  # Reduced to 30 days for free tier
    }
  }
}
