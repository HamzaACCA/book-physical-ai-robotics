#!/bin/bash
# Railway CLI Command - Set All Variables at Once
# Run this after: railway login && railway link

railway variables set \
  GEMINI_API_KEY="AIzaSyDgmhw5VUWVQFlSuqOSrvK8j6cz1FhqapA" \
  GEMINI_EMBEDDING_MODEL="models/text-embedding-004" \
  GEMINI_LLM_MODEL="gemini-1.5-flash" \
  GEMINI_TEMPERATURE="0.3" \
  QDRANT_URL="https://a44bcc35-e2f6-44f0-8a9c-82bb1d13e8f6.us-east4-0.gcp.cloud.qdrant.io" \
  QDRANT_API_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.b4PSGhupOADwbfNZObErXy0s_hfh9uCiDImu7Y2VpjU" \
  QDRANT_COLLECTION_NAME="Hackhaton1" \
  QDRANT_VECTOR_SIZE="768" \
  DATABASE_URL="postgresql://neondb_owner:npg_r8MH4dVSPpgJ@ep-patient-tree-adr5pn76-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require" \
  DATABASE_POOL_MIN_SIZE="2" \
  DATABASE_POOL_MAX_SIZE="10" \
  API_HOST="0.0.0.0" \
  API_PORT="8000" \
  API_RELOAD="false" \
  API_CORS_ORIGINS='["https://hamzaacca.github.io"]' \
  ADMIN_API_KEY="hackathon-admin-key-2024" \
  LOG_LEVEL="INFO"
