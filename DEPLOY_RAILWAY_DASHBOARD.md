# Railway Deployment via Dashboard (WSL-Friendly)

Since you're on WSL, using the Railway dashboard is simpler than CLI authentication.

## Step 1: Create Project on Railway

1. Go to: https://railway.app/dashboard
2. Click **"New Project"**
3. Select **"Empty Project"**
4. Name it: `book-physical-ai-backend`

## Step 2: Connect GitHub Repository

1. In your project, click **"New"** → **"GitHub Repo"**
2. Select your repository
3. Choose branch: **`backend`**
4. Railway will auto-detect it as a Python project

## Step 3: Set Environment Variables

1. Click on your service
2. Go to **"Variables"** tab
3. Click **"Raw Editor"** (easier for bulk paste)
4. Paste this:

```env
GEMINI_API_KEY=AIzaSyDgmhw5VUWVQFlSuqOSrvK8j6cz1FhqapA
GEMINI_EMBEDDING_MODEL=models/text-embedding-004
GEMINI_LLM_MODEL=gemini-1.5-flash
GEMINI_TEMPERATURE=0.3
QDRANT_URL=https://a44bcc35-e2f6-44f0-8a9c-82bb1d13e8f6.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.b4PSGhupOADwbfNZObErXy0s_hfh9uCiDImu7Y2VpjU
QDRANT_COLLECTION_NAME=Hackhaton1
QDRANT_VECTOR_SIZE=768
DATABASE_URL=postgresql://neondb_owner:npg_r8MH4dVSPpgJ@ep-patient-tree-adr5pn76-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require
DATABASE_POOL_MIN_SIZE=2
DATABASE_POOL_MAX_SIZE=10
API_HOST=0.0.0.0
API_PORT=8000
API_RELOAD=false
API_CORS_ORIGINS=["https://hamzaacca.github.io"]
ADMIN_API_KEY=hackathon-admin-key-2024
LOG_LEVEL=INFO
```

5. Click **"Save"** or **"Add"**

## Step 4: Deploy

Railway will automatically deploy when you:
- Push to the `backend` branch, OR
- Click **"Deploy"** button in the dashboard

## Step 5: Monitor Deployment

1. Go to **"Deployments"** tab
2. Watch the build logs
3. Wait for status: **"SUCCESS"** ✅

Expected build output:
```
nixpacks: Building with Python 3.12
uv: Installing dependencies
Starting: uv run python -m backend.src.api.main
Server running on :8000
```

## Step 6: Get Your Deployment URL

1. Go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**
4. Copy the URL (e.g., `https://your-app.up.railway.app`)

## Step 7: Test Deployment

From WSL terminal:

```bash
# Set your Railway URL
export RAILWAY_URL="your-app.up.railway.app"

# Test health
curl https://$RAILWAY_URL/health

# Test chat
curl -X POST https://$RAILWAY_URL/api/v1/chat/message \
    -H "Content-Type: application/json" \
    -d '{"message": "What is Physical AI?"}' | jq .
```

## Advantages of Dashboard Method

- No CLI authentication issues on WSL
- Visual feedback during deployment
- Easy variable management
- Auto-deploy on git push
- Clear error messages

## After Deployment

Your enhanced RAG chatbot will be live with:
- ✅ Chapter/section metadata in sources
- ✅ Follow-up question generation
- ✅ Query refinement suggestions
- ✅ Retrieval quality metrics

**Next step:** Re-ingest books with markdown headers to populate metadata.
