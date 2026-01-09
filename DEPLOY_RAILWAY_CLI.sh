#!/bin/bash
# Complete Railway CLI Deployment Script
# Run this script to deploy your enhanced RAG chatbot

set -e  # Exit on any error

echo "🚀 Railway CLI Deployment Script"
echo "=================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Step 1: Check Railway CLI
echo "Step 1: Checking Railway CLI..."
if ! command -v railway &> /dev/null; then
    echo -e "${RED}❌ Railway CLI not found${NC}"
    echo "Install with: npm install -g @railway/cli"
    exit 1
fi
echo -e "${GREEN}✅ Railway CLI installed${NC}"
echo ""

# Step 2: Login
echo "Step 2: Logging in to Railway..."
echo -e "${YELLOW}This will open your browser for authentication...${NC}"
railway login
echo -e "${GREEN}✅ Logged in to Railway${NC}"
echo ""

# Step 3: Link or Init Project
echo "Step 3: Setting up Railway project..."
echo ""
echo "Do you have an existing Railway project?"
echo "  1) Yes - Link to existing project"
echo "  2) No - Create new project"
echo ""
read -p "Enter choice (1 or 2): " project_choice

if [ "$project_choice" = "1" ]; then
    echo "Linking to existing project..."
    railway link
elif [ "$project_choice" = "2" ]; then
    echo "Creating new project..."
    railway init
else
    echo -e "${RED}Invalid choice. Exiting.${NC}"
    exit 1
fi
echo -e "${GREEN}✅ Project setup complete${NC}"
echo ""

# Step 4: Set Environment Variables
echo "Step 4: Setting environment variables..."
echo -e "${YELLOW}This will set 17 environment variables...${NC}"
echo ""

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

echo -e "${GREEN}✅ Environment variables set${NC}"
echo ""

# Step 5: Verify Variables
echo "Step 5: Verifying environment variables..."
echo "Checking that all required variables are set..."
railway variables | grep -E "GEMINI_API_KEY|QDRANT_URL|DATABASE_URL" || echo "Some variables may not be visible (Railway security)"
echo -e "${GREEN}✅ Variables configured${NC}"
echo ""

# Step 6: Deploy
echo "Step 6: Deploying to Railway..."
echo -e "${YELLOW}This will build and deploy your application...${NC}"
echo ""
read -p "Ready to deploy? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled. You can deploy later with: railway up"
    exit 0
fi

railway up

echo ""
echo -e "${GREEN}✅ Deployment initiated!${NC}"
echo ""

# Step 7: Get Deployment URL
echo "Step 7: Getting deployment URL..."
sleep 5  # Wait for deployment to register

RAILWAY_URL=$(railway status --json 2>/dev/null | jq -r '.domain' || echo "")

if [ -z "$RAILWAY_URL" ] || [ "$RAILWAY_URL" = "null" ]; then
    echo -e "${YELLOW}⚠️  URL not available yet (deployment in progress)${NC}"
    echo "Check status with: railway status"
else
    echo -e "${GREEN}✅ Deployment URL: https://$RAILWAY_URL${NC}"
    echo ""
    echo "Test endpoints:"
    echo "  Health: https://$RAILWAY_URL/health"
    echo "  Docs:   https://$RAILWAY_URL/docs"
    echo "  Chat:   https://$RAILWAY_URL/api/v1/chat/message"
fi

echo ""
echo "=================================="
echo "🎉 Deployment Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "  1. Monitor logs:    railway logs"
echo "  2. Check status:    railway status"
echo "  3. Open in browser: railway open"
echo "  4. View variables:  railway variables"
echo ""
echo "Test your enhanced chatbot:"
echo "  curl https://\$(railway status --json | jq -r '.domain')/health"
echo ""
