# ⚙️ SETUP GUIDE - What You Need to Configure

This guide lists everything you need to add/configure yourself before deploying.

## 🔴 REQUIRED - Must Configure Before Deployment

### 1. AWS Credentials (LOCAL SETUP)

**Configure AWS CLI with your credentials:**

```powershell
aws configure
```

You'll need:
- **AWS Access Key ID**: Get from AWS Console → IAM → Users → Security Credentials
- **AWS Secret Access Key**: Get when creating access key
- **Default region**: `eu-west-3` (Paris)
- **Output format**: `json`

**How to get AWS credentials:**
1. Go to AWS Console: https://console.aws.amazon.com/
2. Navigate to: IAM → Users → [Your User] → Security Credentials
3. Click "Create access key"
4. Download and save the credentials
5. Run `aws configure` and enter them

---

### 2. GitHub Personal Access Token (REQUIRED)

**Create a GitHub token for CodePipeline:**

1. Go to: https://github.com/settings/tokens
2. Click "Generate new token (classic)"
3. Give it a name: `AWS-CodePipeline-Sample`
4. Select scopes:
   - ✅ `repo` (Full control of private repositories)
   - ✅ `admin:repo_hook` (Full control of repository hooks)
5. Click "Generate token"
6. **COPY THE TOKEN** (you won't see it again!)

**Add to your terraform.tfvars:**
```hcl
github_token = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

---

### 3. Database Password (REQUIRED)

**Change the default database password:**

Edit `terraform/terraform.tfvars`:
```hcl
db_password = "YourSecurePassword123!"
```

⚠️ **Requirements:**
- At least 8 characters
- Must contain: letters, numbers, special characters
- Do NOT use the default password!

---

### 4. Create terraform.tfvars File (REQUIRED)

```powershell
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Then edit `terraform.tfvars` with your values:

```hcl
# AWS Configuration
aws_region = "eu-west-3"

# Project Configuration
project_name = "social-media-api"
environment  = "dev"

# GitHub Configuration (YOUR VALUES)
github_repo_owner = "shady0503"           # ✅ Already correct
github_repo_name  = "Sample"              # ✅ Already correct
github_branch     = "master"              # ✅ Already correct
github_token      = "ghp_YOUR_TOKEN_HERE" # 🔴 CHANGE THIS!

# Staging URL (update after deployment)
staging_url = "http://REPLACE_WITH_STAGING_EC2_IP:8080"

# Database Configuration
db_username = "postgres"
db_password = "YourSecurePassword123!"    # 🔴 CHANGE THIS!
```

---

## 🟡 OPTIONAL - Recommended Configurations

### 5. SSH Key for EC2 Access (OPTIONAL but recommended)

To SSH into EC2 instances for debugging:

**Create SSH key:**
```powershell
ssh-keygen -t rsa -b 4096 -f ~/.ssh/social-media-api-key
```

**Add to Terraform** - Edit `terraform/ec2.tf`:

Find the `aws_launch_template` resources and add:
```hcl
resource "aws_launch_template" "ecs_staging" {
  # ... existing config ...
  
  key_name = "your-key-name"  # Add this line
  
  # ... rest of config ...
}
```

**Upload key to AWS:**
1. Go to EC2 Console → Key Pairs
2. Import public key (~/.ssh/social-media-api-key.pub)
3. Name it and note the name
4. Add the name to terraform

---

### 6. Email for Approval Notifications (OPTIONAL)

After deployment, subscribe to SNS topic:

```powershell
# Get the topic ARN
cd terraform
terraform output approval_topic_arn

# Subscribe your email
aws sns subscribe `
  --topic-arn <TOPIC_ARN_FROM_OUTPUT> `
  --protocol email `
  --notification-endpoint your-email@example.com
```

Confirm the subscription via email.

---

### 7. Budget Alerts (OPTIONAL but recommended)

**Option A: Via AWS Console**
1. Go to AWS Billing → Budgets
2. Create budget
3. Set amount: $10
4. Alert at 80% ($8)

**Option B: Via Terraform**

Edit `terraform/budget.tf` and uncomment the resource:
```hcl
resource "aws_budgets_budget" "monthly_cost" {
  # Remove the comment markers
  # Change email to yours
}
```

---

## 📋 Pre-Deployment Checklist

Before running `terraform apply`, verify:

- [ ] AWS CLI configured (`aws sts get-caller-identity` works)
- [ ] Created `terraform.tfvars` from example
- [ ] GitHub token added to `terraform.tfvars`
- [ ] Database password changed in `terraform.tfvars`
- [ ] Region set to `eu-west-3` (Paris)
- [ ] GitHub repo name is correct (`shady0503/Sample`)

---

## 🚀 Deployment Steps

### Step 1: Initialize Terraform
```powershell
cd terraform
terraform init
```

### Step 2: Verify Configuration
```powershell
terraform validate
```

### Step 3: Review Plan
```powershell
terraform plan
```

Check the output - should show ~30-40 resources to create.

### Step 4: Deploy
```powershell
terraform apply
```

Type `yes` when prompted.

⏱️ **Deployment time**: ~10-15 minutes

---

## 📍 After Deployment

### 1. Get EC2 Instance IPs
```powershell
cd ..\scripts
.\get-instance-ips.ps1
```

### 2. Update Staging URL
Edit `terraform/terraform.tfvars`:
```hcl
staging_url = "http://<STAGING_EC2_IP>:8080"
```

Apply again:
```powershell
cd ..\terraform
terraform apply
```

### 3. Verify Application
```powershell
# Test staging
curl http://<STAGING_EC2_IP>:8080/actuator/health

# Test production
curl http://<PRODUCTION_EC2_IP>:8080/actuator/health
```

### 4. Check Database Connection
```powershell
# Get RDS endpoint
terraform output rds_endpoint

# View application logs
aws logs tail /ecs/social-media-api --follow
```

### 5. Subscribe to Approval Notifications (Optional)
```powershell
terraform output approval_topic_arn
# Then subscribe via SNS (see step 6 above)
```

---

## 🔍 Verify Everything Works

### Check Pipeline
1. Go to AWS Console → CodePipeline
2. Find: `social-media-api-pipeline`
3. Wait for it to trigger (or push a commit to GitHub)

### Check ECS
1. AWS Console → ECS
2. Clusters: `social-media-api-staging` and `social-media-api-production`
3. Both should have 1 running task

### Check RDS
1. AWS Console → RDS
2. Instance: `social-media-api-db`
3. Status should be "Available"

### Check Reports
```powershell
aws s3 ls s3://social-media-api-reports-<ACCOUNT_ID>/
```

---

## ⚠️ Common Issues & Solutions

### Issue: "Invalid AWS Credentials"
**Solution:** Run `aws configure` again

### Issue: "GitHub token invalid"
**Solution:** Generate a new token with correct scopes

### Issue: "Insufficient permissions"
**Solution:** Your AWS user needs these permissions:
- EC2 full access
- ECS full access
- RDS full access
- S3 full access
- IAM (create roles)
- CodePipeline full access
- CodeBuild full access

### Issue: "Cannot connect to database"
**Solution:** 
1. Check RDS security group allows EC2 SG
2. Verify RDS is in "Available" state
3. Check application logs

### Issue: "EC2 instance not appearing"
**Solution:** Wait 2-3 minutes for instance to register with ECS

---

## 💰 Cost Monitoring

After deployment, monitor costs:

```powershell
# Current month estimate
aws ce get-cost-and-usage `
  --time-period Start=2025-10-01,End=2025-10-31 `
  --granularity MONTHLY `
  --metrics BlendedCost

# Free tier usage
# Go to AWS Console → Billing → Free Tier
```

**Expected costs**: $0/month (within free tier limits)

---

## 🧹 Cleanup (When Done Testing)

To destroy all resources:

```powershell
cd terraform
terraform destroy
```

Type `yes` to confirm.

⚠️ **Note:** This will:
- Delete the database (with final snapshot if configured)
- Terminate all EC2 instances
- Delete S3 buckets (after emptying them)
- Remove all infrastructure

---

## 📞 Need Help?

### Documentation Files:
- `README.md` - General overview
- `DATABASE.md` - Database access guide
- `NO_ALB_FREE_TIER.md` - Free tier architecture details
- `FREE_TIER_EC2.md` - Cost breakdown

### AWS Resources:
- Free Tier: https://aws.amazon.com/free/
- Documentation: https://docs.aws.amazon.com/
- Terraform: https://registry.terraform.io/providers/hashicorp/aws/latest/docs

### Check Logs:
```powershell
# ECS application logs
aws logs tail /ecs/social-media-api --follow --region eu-west-3

# CodeBuild logs
aws codebuild list-builds --region eu-west-3
```

---

## ✅ Summary - What YOU Must Add:

1. **AWS Credentials** → Run `aws configure`
2. **GitHub Token** → Create at github.com/settings/tokens
3. **Database Password** → Change in terraform.tfvars
4. **Create terraform.tfvars** → Copy from example file

Everything else is pre-configured for **eu-west-3 (Paris)** and FREE TIER!
