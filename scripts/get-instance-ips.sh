#!/bin/bash

# Script to get EC2 instance public IPs for ECS clusters

echo "======================================"
echo "ECS EC2 Instance Public IPs"
echo "======================================"

echo ""
echo "Staging Environment:"
STAGING_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=social-media-api-staging-ecs-instance" \
            "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].PublicIpAddress' \
  --output text)

if [ -z "$STAGING_IP" ]; then
  echo "  ⚠️  No running staging instance found"
else
  echo "  Public IP: $STAGING_IP"
  echo "  Access URL: http://$STAGING_IP:8080"
  echo "  Health Check: http://$STAGING_IP:8080/actuator/health"
fi

echo ""
echo "Production Environment:"
PROD_IP=$(aws ec2 describe-instances \
  --filters "Name=tag:Name,Values=social-media-api-production-ecs-instance" \
            "Name=instance-state-name,Values=running" \
  --query 'Reservations[*].Instances[*].PublicIpAddress' \
  --output text)

if [ -z "$PROD_IP" ]; then
  echo "  ⚠️  No running production instance found"
else
  echo "  Public IP: $PROD_IP"
  echo "  Access URL: http://$PROD_IP:8080"
  echo "  Health Check: http://$PROD_IP:8080/actuator/health"
fi

echo ""
echo "======================================"
echo "Testing Connectivity..."
echo "======================================"

if [ ! -z "$STAGING_IP" ]; then
  echo ""
  echo "Testing Staging..."
  curl -s -o /dev/null -w "  Status: %{http_code}\n" http://$STAGING_IP:8080/actuator/health || echo "  ❌ Connection failed"
fi

if [ ! -z "$PROD_IP" ]; then
  echo ""
  echo "Testing Production..."
  curl -s -o /dev/null -w "  Status: %{http_code}\n" http://$PROD_IP:8080/actuator/health || echo "  ❌ Connection failed"
fi

echo ""
