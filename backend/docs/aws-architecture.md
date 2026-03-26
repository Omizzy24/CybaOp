# CybaOp AWS Architecture — Deployment & SAA Study Reference

This document serves two purposes:
1. Real deployment plan for CybaOp on AWS
2. SAA-C03 exam study reference — each section maps to an exam domain

---

## Architecture Overview

```
                    ┌─────────────┐
                    │  Route 53   │  ← DNS (cybaop.io)
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │ CloudFront  │  ← CDN + WAF attached
                    └──────┬──────┘
                           │
              ┌────────────┼────────────┐
              │                         │
       ┌──────▼──────┐          ┌──────▼──────┐
       │  S3 Bucket  │          │ ALB (API)   │
       │  (Next.js)  │          │ /auth/*     │
       │  Static     │          │ /analytics/*│
       └─────────────┘          └──────┬──────┘
                                       │
                                ┌──────▼──────┐
                                │ ECS Fargate │
                                │ (FastAPI)   │
                                └──────┬──────┘
                                       │
                          ┌────────────┼────────────┐
                          │                         │
                   ┌──────▼──────┐          ┌──────▼──────┐
                   │ RDS Postgres│          │ ElastiCache │
                   │ (Multi-AZ)  │          │ (Redis)     │
                   └─────────────┘          └─────────────┘
```

---

## SAA Domain 1: Secure Architectures (30%)

This is the highest-weighted domain. CybaOp touches it everywhere.

### IAM Design
- **ECS Task Role**: Allows Fargate containers to access RDS, ElastiCache,
  Secrets Manager. No access keys in code — ever.
- **Execution Role**: Allows ECS to pull images from ECR and write to CloudWatch Logs.
- **S3 Bucket Policy**: CloudFront OAC (Origin Access Control) only.
  No public access on the bucket itself.

```
SAA Exam Pattern: "Which is the MOST secure way to allow EC2/ECS to access S3?"
Answer: IAM Role attached to the task/instance — never access keys.
```

### Secrets Management
- SoundCloud OAuth creds → **AWS Secrets Manager** (not env vars, not SSM)
- JWT secret → Secrets Manager, rotated every 90 days
- Database password → Secrets Manager with RDS integration (auto-rotation)

```
SAA Exam Pattern: "How to store database credentials securely?"
Answer: Secrets Manager with automatic rotation enabled.
SSM Parameter Store (SecureString) is cheaper but doesn't auto-rotate.
```

### Network Security
- VPC with public + private subnets across 2 AZs
- ALB in public subnets (internet-facing)
- ECS Fargate tasks in **private subnets** (no public IP)
- RDS + ElastiCache in **private subnets** (no internet access)
- NAT Gateway in public subnet for outbound (SoundCloud API calls from Fargate)

```
SAA Exam Pattern: "Application in private subnet needs to call external API"
Answer: NAT Gateway in public subnet, route table on private subnet points to it.
NOT a NAT Instance (legacy), NOT an Internet Gateway (that makes it public).
```

### WAF Configuration
- Attached to CloudFront distribution (not ALB — CloudFront is the edge)
- Rules:
  - Rate limiting: 1000 req/5min per IP
  - SQL injection protection (managed rule group)
  - Bot control (managed rule group)
  - Geo-restriction: block known bad regions if needed

```
SAA Exam Pattern: "Where to attach WAF for a CloudFront + ALB architecture?"
Answer: CloudFront. WAF at the edge blocks traffic before it reaches your infra.
You CAN attach WAF to ALB too, but CloudFront is the exam-preferred answer.
```

---

## SAA Domain 2: Resilient Architectures (26%)

### Multi-AZ Everything
- RDS: Multi-AZ deployment (synchronous standby, automatic failover)
- ECS: Tasks spread across 2+ AZs via service scheduler
- ALB: Cross-zone load balancing enabled by default
- ElastiCache: Redis cluster mode with replicas in different AZs

```
SAA Exam Pattern: "How to ensure database availability during AZ failure?"
Answer: RDS Multi-AZ. NOT read replicas (those are for read scaling, not HA).
Multi-AZ = synchronous replication + automatic failover.
Read Replica = async replication, manual promotion.
```

### Health Checks & Auto-Recovery
- ALB health check → `/health` endpoint on FastAPI (already built)
- ECS service: desired count = 2, minimum healthy = 1
- If a task fails health check → ECS replaces it automatically
- RDS: automatic failover to standby (typically 60-120 seconds)

### Backup Strategy
- RDS: Automated backups (35-day retention) + manual snapshots before deploys
- S3: Versioning enabled on the static assets bucket
- No need for cross-region replication unless we go multi-region later

```
SAA Exam Pattern: "RPO of 1 hour, RTO of 15 minutes — which backup strategy?"
Answer: RDS automated backups (continuous, point-in-time recovery).
For RPO=0: Multi-AZ (synchronous). For cross-region DR: cross-region read replica.
```

---

## SAA Domain 3: High-Performing Architectures (24%)

### CloudFront + S3 (Static Layer)
- Next.js exported as static site → S3 bucket
- CloudFront distribution with:
  - Custom domain via Route 53 alias record
  - ACM certificate (us-east-1, required for CloudFront)
  - Cache behaviors:
    - `/_next/static/*` → cache 1 year (immutable hashes)
    - `/*.html` → cache 5 min with stale-while-revalidate
    - `/api/*` → forward to ALB origin (no caching)

```
SAA Exam Pattern: "ACM certificate for CloudFront must be in which region?"
Answer: us-east-1. Always. Even if your ALB is in us-west-2.
```

### API Layer (ECS Fargate)
- Fargate spot for dev/staging (70% cheaper, acceptable interruption)
- Fargate on-demand for production
- Task size: 0.5 vCPU, 1GB RAM (FastAPI is lightweight)
- Auto-scaling: target tracking on CPU (50%) and request count per target

```
SAA Exam Pattern: "Cost-effective compute for stateless API containers?"
Answer: Fargate Spot for non-critical, Fargate on-demand for production.
Lambda is cheaper at low traffic but has cold start issues for APIs.
```

### Database Performance
- RDS Postgres (db.t4g.medium for start — ARM-based, cheaper)
- Connection pooling: RDS Proxy (solves Fargate's connection churn problem)
- Read replica for analytics queries (separate from auth/write path)

```
SAA Exam Pattern: "Serverless/container app has too many DB connections"
Answer: RDS Proxy. It pools and multiplexes connections.
NOT increasing max_connections (that's a band-aid).
```

### Caching Layer
- ElastiCache Redis for:
  - Profile data cache (TTL: 1 hour, already defined in config)
  - Track data cache (TTL: 30 min)
  - Rate limiting counters (sliding window)
- Cache-aside pattern: check Redis → miss → fetch from SoundCloud → store in Redis

```
SAA Exam Pattern: "Reduce load on database for frequently read data?"
Answer: ElastiCache (Redis or Memcached). Redis if you need persistence/pub-sub.
DAX is only for DynamoDB. CloudFront is for static content, not DB queries.
```

---

## SAA Domain 4: Cost-Optimized Architectures (20%)

### Compute Costs
| Component | Dev | Production |
|-----------|-----|------------|
| ECS Fargate | Spot, 1 task | On-demand, 2 tasks |
| RDS | db.t4g.micro, single-AZ | db.t4g.medium, Multi-AZ |
| ElastiCache | cache.t4g.micro | cache.t4g.small |
| NAT Gateway | 1 (single AZ ok for dev) | 1 per AZ |

### Estimated Monthly Cost
- **Dev/Staging**: ~$50-80/month
  - Fargate Spot: ~$10
  - RDS single-AZ micro: ~$15
  - ElastiCache micro: ~$12
  - NAT Gateway: ~$35 (this is the expensive part)
- **Production**: ~$200-300/month
  - Fargate on-demand (2 tasks): ~$30
  - RDS Multi-AZ medium: ~$70
  - ElastiCache small: ~$25
  - NAT Gateway (2): ~$70
  - CloudFront: ~$5-10 (low traffic)

```
SAA Exam Pattern: "Reduce NAT Gateway costs?"
Answer: VPC endpoints for AWS services (S3, DynamoDB, ECR, CloudWatch).
Gateway endpoints (S3, DynamoDB) are free. Interface endpoints cost ~$7/month each.
NAT Gateway charges per GB processed — VPC endpoints bypass it for AWS traffic.
```

### Cost Optimization Tactics
- S3 Intelligent-Tiering for static assets (auto-moves infrequent objects)
- Reserved Instances for RDS if committed for 1+ year (40% savings)
- Savings Plans for Fargate (up to 50% savings on committed usage)
- CloudWatch Logs: set retention to 30 days (not infinite)

---

## Deployment Pipeline

```
GitHub (feature/backend-api)
    │
    ▼
GitHub Actions
    ├── Build Next.js → S3 sync + CloudFront invalidation
    └── Build Docker → ECR push → ECS service update
```

### Infrastructure as Code
- Terraform for all AWS resources
- Separate state files: `network`, `data`, `compute`, `cdn`
- Environment separation via Terraform workspaces or separate tfvars

---

## What This Covers on the SAA-C03

| Exam Domain | Weight | CybaOp Components |
|-------------|--------|--------------------|
| Secure Architectures | 30% | IAM roles, Secrets Manager, VPC design, WAF, OAC |
| Resilient Architectures | 26% | Multi-AZ RDS, ECS health checks, ALB, backups |
| High-Performing | 24% | CloudFront, ElastiCache, RDS Proxy, auto-scaling |
| Cost-Optimized | 20% | Fargate Spot, Reserved Instances, VPC endpoints |

Every component in this architecture maps to exam questions you will see.
Build it, and you'll have hands-on answers for ~60% of the exam.
