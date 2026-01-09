# Railway Deployment Guide

## 🚀 Deploy Enhanced RAG Chatbot to Railway

Your enhanced features are ready to deploy! Follow these steps to get your chatbot live on Railway.

---

## Prerequisites Checklist

- [x] Code committed to `backend` branch
- [x] Railway configuration files present:
  - `railway.json` ✅
  - `nixpacks.toml` ✅
  - `Dockerfile` ✅
- [x] Environment variables ready (see below)
- [ ] Railway CLI installed (`railway` command available)
- [ ] Logged into Railway account

---

## Step 1: Login to Railway

Open your terminal and run:

```bash
railway login
```

This will:
1. Open a browser window
2. Ask you to authenticate with your Railway account
3. Store credentials locally

**Expected output:**
```
🎉 Logged in as your-email@example.com
```

---

## Step 2: Link to Railway Project

### Option A: If you already have a Railway project

```bash
# Link to existing project
railway link

# Follow the prompts to select your project
```

### Option B: Create a new Railway project

```bash
# Create new project
railway init

# Enter project name: book-physical-ai-backend
# Select starter: Empty Project
```

---

## Step 3: Set Environment Variables

Railway needs your API keys and database credentials. Set them using the Railway CLI or dashboard.

### Via Railway CLI (Recommended for bulk setup):

```bash
# Set all environment variables at once
railway variables set \
  GEMINI_API_KEY="your_gemini_api_key_here" \
  GEMINI_EMBEDDING_MODEL="models/text-embedding-004" \
  GEMINI_LLM_MODEL="gemini-1.5-flash" \
  GEMINI_TEMPERATURE="0.3" \
  QDRANT_URL="your_qdrant_cluster_url" \
  QDRANT_API_KEY="your_qdrant_api_key" \
  QDRANT_COLLECTION_NAME="Hackhaton1" \
  QDRANT_VECTOR_SIZE="768" \
  DATABASE_URL="your_neon_postgres_url" \
  DATABASE_POOL_MIN_SIZE="2" \
  DATABASE_POOL_MAX_SIZE="10" \
  API_HOST="0.0.0.0" \
  API_PORT="8000" \
  API_RELOAD="false" \
  API_CORS_ORIGINS='["https://hamzaacca.github.io"]' \
  ADMIN_API_KEY="hackathon-admin-key-2024" \
  LOG_LEVEL="INFO"
```

### Via Railway Dashboard (Easier for first-time setup):

1. Go to https://railway.app/dashboard
2. Select your project
3. Click on **Variables** tab
4. Add each variable manually:

**Required Variables:**

| Variable | Value | Notes |
|----------|-------|-------|
| `GEMINI_API_KEY` | Your Gemini API key | From Google AI Studio |
| `GEMINI_EMBEDDING_MODEL` | `models/text-embedding-004` | Fixed value |
| `GEMINI_LLM_MODEL` | `gemini-1.5-flash` | Or `gemini-1.5-pro` |
| `QDRANT_URL` | Your Qdrant cluster URL | From Qdrant Cloud |
| `QDRANT_API_KEY` | Your Qdrant API key | From Qdrant Cloud |
| `QDRANT_COLLECTION_NAME` | `Hackhaton1` | Your collection name |
| `QDRANT_VECTOR_SIZE` | `768` | For text-embedding-004 |
| `DATABASE_URL` | Your Neon Postgres URL | From Neon dashboard |
| `API_CORS_ORIGINS` | `["https://hamzaacca.github.io"]` | Your frontend URL |

**Optional Variables:**

| Variable | Default | Notes |
|----------|---------|-------|
| `DATABASE_POOL_MIN_SIZE` | `2` | Min connections |
| `DATABASE_POOL_MAX_SIZE` | `10` | Max connections |
| `API_HOST` | `0.0.0.0` | Bind to all interfaces |
| `API_PORT` | `8000` | Railway auto-detects |
| `API_RELOAD` | `false` | No hot reload in prod |
| `ADMIN_API_KEY` | Your secret | For admin endpoints |
| `LOG_LEVEL` | `INFO` | DEBUG, INFO, WARNING, ERROR |

---

## Step 4: Deploy to Railway

### Option A: Deploy from GitHub (Recommended)

Railway can auto-deploy on every git push!

1. **Connect GitHub repository:**
   ```bash
   railway connect
   # Or via dashboard: Settings → Connect GitHub Repo
   ```

2. **Select branch:**
   - Branch: `backend`
   - Root Directory: `/` (or leave empty)

3. **Deploy automatically:**
   ```bash
   git push origin backend
   # Railway auto-deploys!
   ```

### Option B: Deploy directly with Railway CLI

```bash
# Deploy current code
railway up

# This will:
# - Build using nixpacks
# - Install dependencies with uv
# - Start the FastAPI server
```

### Option C: Deploy via Railway Dashboard

1. Go to https://railway.app/dashboard
2. Select your project
3. Click **Deploy** → **Deploy Now**

---

## Step 5: Monitor Deployment

### Check Build Logs:

```bash
# Stream deployment logs
railway logs

# Or via dashboard: Deployments → Latest → Logs
```

**Expected build output:**
```
--> Installing with nixpacks
--> Python 3.12 detected
--> Installing uv
--> Running: uv sync
--> Starting: uv run python -m backend.src.api.main
✓ Server started on http://0.0.0.0:8000
```

### Check Deployment Status:

```bash
# Get deployment URL
railway status

# Or via dashboard: Deployments → Latest
```

**Expected output:**
```
Project: book-physical-ai-backend
Service: backend
Status: DEPLOYED ✓
URL: https://your-app.up.railway.app
```

---

## Step 6: Verify Deployment

### Test Health Endpoint:

```bash
# Get your Railway URL
export RAILWAY_URL=$(railway status --json | jq -r '.domain')

# Test health endpoint
curl https://$RAILWAY_URL/health

# Expected response:
# {"status": "healthy"}
```

**Or manually:**
```bash
curl https://your-app.up.railway.app/health
```

### Test Chat Endpoint:

```bash
curl -X POST https://$RAILWAY_URL/api/v1/chat/message \
    -H "Content-Type: application/json" \
    -d '{
        "message": "What is Physical AI?"
    }' | jq .
```

**Expected response with enhanced features:**
```json
{
  "answer": "Physical AI is...",
  "session_id": "...",
  "sources": [
    {
      "chunk_id": "...",
      "text_preview": "...",
      "similarity": 0.85,
      "chapter_title": "Introduction to Physical AI",
      "section_title": "Core Concepts"
    }
  ],
  "follow_up_questions": [
    "What are the main applications...",
    "How does Physical AI differ...",
    "What tools are used..."
  ],
  "retrieval_quality": 0.82
}
```

---

## Troubleshooting

### Issue: Build fails with "Python not detected"

**Solution:** Ensure `nixpacks.toml` is in the root directory:
```bash
ls -la nixpacks.toml
# Should exist at project root
```

### Issue: "Module not found" error

**Solution:** Ensure `pyproject.toml` has all dependencies:
```bash
cat pyproject.toml | grep google-generativeai
# Should show: "google-generativeai>=0.3.2"
```

### Issue: Health check fails

**Solution:** Check if `/health` endpoint is accessible:
```bash
railway logs | grep health
# Should show: GET /health → 200 OK
```

### Issue: Environment variables not loading

**Solution:** Verify variables are set:
```bash
railway variables
# Should list all env vars
```

### Issue: Database connection fails

**Solution:** Check DATABASE_URL format:
```bash
railway variables get DATABASE_URL
# Should be: postgresql://user:pass@host/db?sslmode=require
```

---

## Configuration Files Explained

### `railway.json` - Railway Deployment Config

```json
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "uv sync"
  },
  "deploy": {
    "startCommand": "uv run python -m backend.src.api.main",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 300,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 3
  }
}
```

**Key settings:**
- **Builder:** Nixpacks (automatic Python detection)
- **Build:** `uv sync` (fast dependency installation)
- **Start:** Runs FastAPI via uv
- **Health:** Checks `/health` endpoint every 30s
- **Restart:** Auto-restarts on failures (max 3 retries)

### `nixpacks.toml` - Build Configuration

```toml
[providers]
python = "3.12"

[phases.install]
cmds = ["pip install uv", "uv sync"]

[start]
cmd = "uv run python -m backend.src.api.main"
```

**Key settings:**
- **Python:** 3.12 (latest stable)
- **Package manager:** uv (faster than pip)
- **Dependencies:** Auto-synced from pyproject.toml

---

## Post-Deployment Checklist

After successful deployment:

- [ ] Health endpoint responding: `https://your-app.railway.app/health`
- [ ] API docs accessible: `https://your-app.railway.app/docs`
- [ ] Chat endpoint working with enhanced features
- [ ] Neon database connected (check logs)
- [ ] Qdrant vector search working
- [ ] CORS configured for your frontend
- [ ] Environment variables secured (not in git)

---

## Next Steps After Deployment

### 1. Re-ingest Books with Markdown

To populate chapter/section metadata:

```bash
# Create markdown version of your book
cat > physical-ai-book.md <<EOF
# Chapter 1: Introduction to Physical AI

Content here...

## What is Physical AI?

More content...

# Chapter 2: Hardware Requirements

Content here...
EOF

# Ingest via API (from your local machine)
curl -X POST https://your-app.railway.app/api/v1/admin/ingest \
    -H "Content-Type: application/json" \
    -H "X-Admin-Key: your-admin-key" \
    -d '{
        "file_url": "https://your-storage.com/book.md",
        "book_title": "Physical AI Guide"
    }'
```

### 2. Update Frontend to Use Enhanced Features

Update your frontend to display:
- Chapter/section citations
- Follow-up questions
- Query suggestions
- Retrieval quality score

### 3. Monitor Performance

```bash
# Watch logs in real-time
railway logs --follow

# Check for:
# - Response times
# - Follow-up generation latency
# - Error rates
```

---

## Quick Reference Commands

```bash
# Login
railway login

# Link project
railway link

# Set variables
railway variables set KEY=value

# Deploy
railway up

# Check status
railway status

# View logs
railway logs

# Open in browser
railway open

# SSH into container
railway shell
```

---

## Support & Resources

- **Railway Docs:** https://docs.railway.app
- **Railway Status:** https://status.railway.app
- **Project Dashboard:** https://railway.app/dashboard
- **Build Logs:** Check deployment logs for errors
- **Community:** Railway Discord for help

---

## Deployment Status

**Current State:**
- ✅ Code committed to `backend` branch
- ✅ Configuration files ready
- ✅ Enhanced features implemented
- ⏳ Waiting for Railway deployment
- ⏳ Environment variables to be set

**After Deployment:**
- 🎯 Test enhanced chat features
- 🎯 Re-ingest books with markdown
- 🎯 Verify metadata appears in responses
- 🎯 Monitor performance and logs

---

**Last Updated:** 2026-01-09
**Branch:** backend
**Latest Commit:** ba75076 - Add comprehensive feature implementation documentation
