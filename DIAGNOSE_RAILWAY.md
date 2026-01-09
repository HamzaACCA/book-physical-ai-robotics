# Railway Deployment Diagnostics

Your app deployed successfully but getting connection errors.

## Error Observed:
```
SSL connection has been closed unexpectedly
```

This indicates a database connection issue (Qdrant or Neon PostgreSQL).

## Check These in Railway Dashboard:

### 1. Verify Environment Variables Are Set

Go to: **Your Service → Variables Tab**

Check that ALL these variables exist:

**Critical Variables:**
- ✅ `DATABASE_URL` - PostgreSQL connection string
- ✅ `QDRANT_URL` - Qdrant cluster URL
- ✅ `QDRANT_API_KEY` - Qdrant authentication
- ✅ `GEMINI_API_KEY` - Google AI API key

**Expected Values:**
```
DATABASE_URL=postgresql://neondb_owner:npg_r8MH4dVSPpgJ@ep-patient-tree-adr5pn76-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require
QDRANT_URL=https://a44bcc35-e2f6-44f0-8a9c-82bb1d13e8f6.us-east4-0.gcp.cloud.qdrant.io
QDRANT_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.b4PSGhupOADwbfNZObErXy0s_hfh9uCiDImu7Y2VpjU
GEMINI_API_KEY=AIzaSyDgmhw5VUWVQFlSuqOSrvK8j6cz1FhqapA
```

### 2. Check Deployment Logs

Go to: **Deployments Tab → Latest Deployment → View Logs**

Look for errors like:
- `Failed to connect to database`
- `Qdrant connection refused`
- `SSL error`
- `Authentication failed`

### 3. Common Issues:

**Issue: Variables Not Set**
- Solution: Go to Variables tab, click "Raw Editor"
- Paste all variables from `RAILWAY_ENV_VARS.txt`
- Click Save

**Issue: Wrong SSL Mode**
- Check if `DATABASE_URL` ends with `?sslmode=require`
- Neon requires SSL connections

**Issue: Qdrant API Key Expired**
- Check if Qdrant cluster is still active
- Verify API key hasn't been rotated

**Issue: Network/Firewall**
- Ensure Qdrant cluster allows connections from Railway IPs
- Check Neon database isn't paused

### 4. Quick Variable Check Command

In Railway Dashboard → Service → **Variables tab**, verify you have exactly **17 variables**:

1. GEMINI_API_KEY
2. GEMINI_EMBEDDING_MODEL
3. GEMINI_LLM_MODEL
4. GEMINI_TEMPERATURE
5. QDRANT_URL
6. QDRANT_API_KEY
7. QDRANT_COLLECTION_NAME
8. QDRANT_VECTOR_SIZE
9. DATABASE_URL
10. DATABASE_POOL_MIN_SIZE
11. DATABASE_POOL_MAX_SIZE
12. API_HOST
13. API_PORT
14. API_RELOAD
15. API_CORS_ORIGINS
16. ADMIN_API_KEY
17. LOG_LEVEL

### 5. Force Redeploy After Setting Variables

If you added/fixed variables:
1. Go to **Deployments** tab
2. Click **"Redeploy"** on latest deployment
3. Or: Make a trivial change and push to GitHub

### 6. Test Individual Services

**Test Neon PostgreSQL:**
```bash
# From your local machine or WSL
psql "postgresql://neondb_owner:npg_r8MH4dVSPpgJ@ep-patient-tree-adr5pn76-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require" -c "SELECT 1;"
```

**Test Qdrant:**
```bash
curl -H "api-key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.b4PSGhupOADwbfNZObErXy0s_hfh9uCiDImu7Y2VpjU" \
  https://a44bcc35-e2f6-44f0-8a9c-82bb1d13e8f6.us-east4-0.gcp.cloud.qdrant.io/collections/Hackhaton1
```

## Next Steps:

1. **Check Railway Variables** (most likely cause)
2. **View deployment logs** for specific error
3. **Redeploy** after fixing variables
4. **Report back** with what you find

---

## If Variables Are Missing:

Copy all variables from `RAILWAY_ENV_VARS.txt` or use this quick command format:

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
API_PORT=8000
API_RELOAD=false
API_CORS_ORIGINS=["https://hamzaacca.github.io"]
ADMIN_API_KEY=hackathon-admin-key-2024
LOG_LEVEL=INFO
```

Paste this in Railway's **Raw Editor** under Variables tab.
