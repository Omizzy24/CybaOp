---
inclusion: manual
---

# Deployment Context

## Live Infrastructure
- Frontend: Vercel — `https://cyba-op.vercel.app`
- Backend: Railway — `https://delightful-beauty-production-7537.up.railway.app`
- Database: Neon Postgres — `ep-restless-union-a40o6rwu-pooler.us-east-1.aws.neon.tech`
- Branch: `feature/backend-api` (auto-deploys on push)

## Deployment Flow
- Push to `feature/backend-api` → Railway rebuilds backend (Dockerfile in `backend/`)
- Push to `feature/backend-api` → Vercel rebuilds frontend (root Next.js app)
- Both auto-deploy, no manual trigger needed after initial setup

## Environment Variables
### Railway (backend)
- DATABASE_URL, SOUNDCLOUD_CLIENT_ID, SOUNDCLOUD_CLIENT_SECRET
- SOUNDCLOUD_REDIRECT_URI, FRONTEND_URL, JWT_SECRET, ENV, LOG_LEVEL

### Vercel (frontend)
- BACKEND_URL, SOUNDCLOUD_CLIENT_ID, SOUNDCLOUD_CLIENT_SECRET
- SOUNDCLOUD_REDIRECT_URI, NEXT_PUBLIC_BASE_URL

## Common Issues
- Railway scans root package.json if root directory isn't set to `backend`
- Neon connection strings have `channel_binding=require` — asyncpg can't handle it, we strip query params
- Next.js version must stay patched for CVEs or both Vercel and Railway reject deploys
- SoundCloud redirect URI must match exactly in: Vercel env, Railway env, and SoundCloud app settings
