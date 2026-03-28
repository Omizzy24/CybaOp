# CybaOp AWS Migration Prompt

You are a senior cloud architect migrating CybaOp from Railway/Neon to AWS-native infrastructure.

## CURRENT STATE

| Component | Current | Target |
|-----------|---------|--------|
| Frontend | Vercel (keep) | Vercel (no change) |
| Backend | Railway (FastAPI container) | ECS Fargate |
| Database | Neon Postgres (serverless) | RDS Postgres (Multi-AZ) |
| CDN/DDoS | Vercel edge only | CloudFront + WAF |
| DNS | Vercel auto | Route 53 |
| Secrets | Railway env vars | Secrets Manager |
| Container Registry | Railway auto | ECR |
| Monitoring | None | CloudWatch |

## WHY MIGRATE

1. Railway free tier has cold starts that kill OAuth flows
2. No DDoS protection on the backend
3. No spending caps — Railway charges when credits run out
4. No horizontal scaling — single container
5. SAA certification study — building this on AWS is hands-on exam prep

## ARCHITECTURE

```
Internet
  │
  ├── cyba-op.vercel.app (frontend, stays on Vercel)
  │     └── /api/* routes proxy to ALB
  │
  └── api.cybaop.io (Route 53 → CloudFront → ALB)
        │
        CloudFront (CDN + WAF)
        │  ├── Rate limiting: 1000 req/5min per IP
        │  ├── SQL injection protection (managed rules)
        │  └── Bot control
        │
        ALB (Application Load Balancer)
        │  ├── Health check: GET /health
        │  └── Target: ECS Fargate service
        │
        ECS Fargate (FastAPI container)
        │  ├── Task: 0.5 vCPU, 1GB RAM
        │  ├── Desired count: 2 (Multi-AZ)
        │  ├── Auto-scaling: CPU 50% target
        │  ├── IAM Task Role: access Secrets Manager, RDS, CloudWatch
        │  └── Image from ECR
        │
        RDS Postgres (Multi-AZ)
        │  ├── db.t4g.micro (free tier eligible)
        │  ├── Automated backups: 7 days
        │  ├── Connection via RDS Proxy (pool connections)
        │  └── Private subnet only
        │
        Secrets Manager
           ├── SOUNDCLOUD_CLIENT_ID
           ├── SOUNDCLOUD_CLIENT_SECRET
           ├── JWT_SECRET
           └── DATABASE_URL (auto-generated from RDS)
```

## IMPLEMENTATION TASKS

### Task 1: Terraform Foundation

Create `infra/` directory with Terraform modules:

```
infra/
├── main.tf              # Provider, backend config
├── variables.tf         # Input variables
├── outputs.tf           # ALB URL, ECR repo, etc.
├── modules/
│   ├── network/         # VPC, subnets, NAT gateway
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── database/        # RDS, security group
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   ├── compute/         # ECR, ECS, ALB, auto-scaling
│   │   ├── main.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   └── cdn/             # CloudFront, WAF, Route 53
│       ├── main.tf
│       ├── variables.tf
│       └── outputs.tf
├── environments/
│   ├── dev.tfvars
│   └── prod.tfvars
└── .github/
    └── workflows/
        └── deploy.yml   # GitHub Actions CI/CD
```

### Task 2: Network Module

- VPC: 10.0.0.0/16
- Public subnets: 2 AZs (for ALB, NAT Gateway)
- Private subnets: 2 AZs (for ECS, RDS)
- NAT Gateway: 1 (dev), 2 (prod)
- Security groups:
  - ALB: inbound 443 from anywhere
  - ECS: inbound from ALB SG only
  - RDS: inbound 5432 from ECS SG only

### Task 3: Database Module

- RDS Postgres 15, db.t4g.micro
- Multi-AZ: false (dev), true (prod)
- Automated backups: 7 days
- Storage: 20GB gp3
- Credentials in Secrets Manager (auto-rotation)
- Private subnet, no public access
- RDS Proxy for connection pooling

### Task 4: Compute Module

- ECR repository for backend image
- ECS Cluster (Fargate)
- Task definition: 0.5 vCPU, 1GB RAM
- Service: desired 1 (dev), 2 (prod)
- ALB with health check on /health
- Auto-scaling: target tracking on CPU (50%)
- Task role: Secrets Manager read, CloudWatch logs
- Execution role: ECR pull, CloudWatch logs

### Task 5: CDN Module

- CloudFront distribution
- Origin: ALB
- WAF Web ACL:
  - Rate limiting: 1000 req/5min per IP
  - AWS managed rules: SQL injection, XSS
  - Bot control (optional)
- Route 53: A record alias to CloudFront
- ACM certificate in us-east-1

### Task 6: CI/CD Pipeline

GitHub Actions workflow:
1. On push to `main`:
   - Build Docker image
   - Push to ECR
   - Update ECS service (rolling deployment)
2. On push to `feature/*`:
   - Run tests only
3. Terraform plan on PR, apply on merge to `main`

### Task 7: Backend Code Changes

Minimal changes needed:
- Read secrets from Secrets Manager instead of env vars (or use ECS task definition to inject from Secrets Manager as env vars — simpler)
- Update CORS to include CloudFront domain
- Remove Railway-specific config (railway.toml)
- Update Vercel BACKEND_URL to point to CloudFront/ALB URL

## COST ESTIMATE

### Dev Environment (~$30-50/month)
- ECS Fargate: ~$10 (0.5 vCPU, 1GB, always-on)
- RDS t4g.micro: ~$15 (single-AZ, free tier eligible first 12 months)
- NAT Gateway: ~$35 (this is the expensive part)
- CloudFront: ~$1 (low traffic)
- Route 53: ~$0.50/zone
- Secrets Manager: ~$1

### Cost Optimization
- Use VPC endpoints for ECR/CloudWatch/S3 (bypass NAT Gateway for AWS traffic)
- RDS free tier covers first 12 months
- CloudFront free tier: 1TB/month
- Consider NAT Instance instead of NAT Gateway for dev ($3/mo vs $35/mo)

## SAA EXAM RELEVANCE

Every component maps to exam questions:
- VPC design (subnets, NAT, security groups) → Domain 1: Secure Architectures
- Multi-AZ RDS, ECS health checks → Domain 2: Resilient Architectures
- CloudFront, RDS Proxy, auto-scaling → Domain 3: High-Performing
- NAT Gateway costs, Reserved Instances → Domain 4: Cost-Optimized

## CONSTRAINTS

- Do NOT move the frontend off Vercel (it works, it's free, it's fast)
- Do NOT change the backend API contracts
- Do NOT add new backend dependencies
- Terraform state stored in S3 + DynamoDB lock table
- All secrets in Secrets Manager, never in code or tfvars
- Use `us-east-1` region (matches Neon, cheapest)

## STOP CONDITIONS

- If AWS account doesn't have free tier → warn about costs before proceeding
- If domain (cybaop.io) isn't registered → skip Route 53, use ALB URL directly
- If Terraform state backend (S3) doesn't exist → create it first

## DEFINITION OF DONE

1. `terraform apply` creates all infrastructure
2. Docker image builds and pushes to ECR via GitHub Actions
3. ECS service runs and /health returns 200
4. Vercel BACKEND_URL updated to CloudFront/ALB URL
5. Full OAuth flow works through the new backend
6. WAF blocks > 1000 req/5min from single IP
7. RDS contains user data after successful auth
8. CloudWatch shows structured logs from ECS tasks
