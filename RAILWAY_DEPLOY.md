# Railway Deployment Guide

## Quick Deploy Steps

### 1. Push Code to GitHub
```bash
git add .
git commit -m "Add Railway deployment configuration"
git push origin master
```

### 2. Deploy on Railway

1. Go to [railway.app](https://railway.app) and sign in with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository: `book-physical-ai-robotics` or `hackathon1`
4. Railway will automatically detect the configuration

### 3. Add Environment Variables

In Railway dashboard, go to **Variables** tab and add:

```
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
API_RELOAD=false
API_WORKERS=1
API_CORS_ORIGINS=["https://hamzaacca.github.io"]

ADMIN_API_KEY=your-secret-admin-key-here

LOG_LEVEL=INFO
CHUNK_SIZE_TOKENS=800
CHUNK_OVERLAP_TOKENS=128
MIN_SIMILARITY_THRESHOLD=0.7
SESSION_EXPIRATION_MINUTES=30
MAX_CONVERSATION_MESSAGES=10
MAX_RETRIEVED_CHUNKS=5

RATE_LIMIT_REQUESTS_PER_MINUTE=100
```

**Note:** Railway automatically provides `PORT` environment variable.

### 4. Get Your Railway URL

After deployment:
1. Go to **Settings** tab
2. Under **Domains**, you'll see your Railway URL (e.g., `your-app.railway.app`)
3. Copy this URL - you'll need it for the chatbot widget

### 5. Update Chatbot Widget

Edit `/tmp/physical-ai-robotics/static/chat-widget.js`:

```javascript
// Change this line
const API_BASE_URL = 'http://localhost:8000/api/v1/chat';

// To your Railway URL
const API_BASE_URL = 'https://your-app.railway.app/api/v1/chat';
```

### 6. Push Widget Update

```bash
cd /tmp/physical-ai-robotics
git add static/chat-widget.js
git commit -m "Update chatbot to use Railway backend"
git push origin master
```

Wait 1-2 minutes for GitHub Pages to rebuild, then your chatbot will work!

## Testing

Test your deployed API:
```bash
curl https://your-app.railway.app/health
```

Should return:
```json
{"status":"healthy"}
```

## Troubleshooting

### Deployment fails
- Check Railway logs in the dashboard
- Ensure all environment variables are set
- Verify `pyproject.toml` and `uv.lock` are committed

### API returns 500 errors
- Check if database connection is working
- Verify Qdrant credentials
- Check Railway logs for error details

### CORS errors in browser
- Ensure `API_CORS_ORIGINS` includes your GitHub Pages URL
- Check Railway logs for CORS-related errors
