# PowerShell script to get EC2 instance public IPs for ECS clusters

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "ECS EC2 Instance Public IPs" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "Staging Environment:" -ForegroundColor Yellow

$stagingIp = aws ec2 describe-instances `
  --filters "Name=tag:Name,Values=social-media-api-staging-ecs-instance" `
            "Name=instance-state-name,Values=running" `
  --query 'Reservations[*].Instances[*].PublicIpAddress' `
  --output text

if ([string]::IsNullOrWhiteSpace($stagingIp)) {
  Write-Host "  ⚠️  No running staging instance found" -ForegroundColor Red
} else {
  Write-Host "  Public IP: $stagingIp" -ForegroundColor Green
  Write-Host "  Access URL: http://$stagingIp:8080"
  Write-Host "  Health Check: http://$stagingIp:8080/actuator/health"
}

Write-Host ""
Write-Host "Production Environment:" -ForegroundColor Yellow

$prodIp = aws ec2 describe-instances `
  --filters "Name=tag:Name,Values=social-media-api-production-ecs-instance" `
            "Name=instance-state-name,Values=running" `
  --query 'Reservations[*].Instances[*].PublicIpAddress' `
  --output text

if ([string]::IsNullOrWhiteSpace($prodIp)) {
  Write-Host "  ⚠️  No running production instance found" -ForegroundColor Red
} else {
  Write-Host "  Public IP: $prodIp" -ForegroundColor Green
  Write-Host "  Access URL: http://$prodIp:8080"
  Write-Host "  Health Check: http://$prodIp:8080/actuator/health"
}

Write-Host ""
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Testing Connectivity..." -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

if (-not [string]::IsNullOrWhiteSpace($stagingIp)) {
  Write-Host ""
  Write-Host "Testing Staging..." -ForegroundColor Yellow
  try {
    $response = Invoke-WebRequest -Uri "http://$stagingIp:8080/actuator/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
  } catch {
    Write-Host "  ❌ Connection failed: $_" -ForegroundColor Red
  }
}

if (-not [string]::IsNullOrWhiteSpace($prodIp)) {
  Write-Host ""
  Write-Host "Testing Production..." -ForegroundColor Yellow
  try {
    $response = Invoke-WebRequest -Uri "http://$prodIp:8080/actuator/health" -UseBasicParsing -TimeoutSec 5
    Write-Host "  Status: $($response.StatusCode)" -ForegroundColor Green
  } catch {
    Write-Host "  ❌ Connection failed: $_" -ForegroundColor Red
  }
}

Write-Host ""
