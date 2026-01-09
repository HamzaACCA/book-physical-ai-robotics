#!/bin/bash
# Verify Railway Deployment
# Run this after deployment completes

set -e

echo "🔍 Verifying Railway Deployment"
echo "================================"
echo ""

# Get deployment URL
echo "1. Getting deployment URL..."
RAILWAY_URL=$(railway status --json 2>/dev/null | jq -r '.domain' || echo "")

if [ -z "$RAILWAY_URL" ] || [ "$RAILWAY_URL" = "null" ]; then
    echo "❌ Could not get deployment URL"
    echo "   Check status with: railway status"
    exit 1
fi

echo "✅ Deployment URL: https://$RAILWAY_URL"
echo ""

# Test health endpoint
echo "2. Testing health endpoint..."
HEALTH_RESPONSE=$(curl -s "https://$RAILWAY_URL/health" || echo "")

if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
    echo "✅ Health check passed"
    echo "   Response: $HEALTH_RESPONSE"
else
    echo "❌ Health check failed"
    echo "   Response: $HEALTH_RESPONSE"
    exit 1
fi
echo ""

# Test chat endpoint with enhanced features
echo "3. Testing enhanced chat endpoint..."
CHAT_RESPONSE=$(curl -s -X POST "https://$RAILWAY_URL/api/v1/chat/message" \
    -H "Content-Type: application/json" \
    -d '{"message": "What is Physical AI?"}' || echo "")

echo "Response preview:"
echo "$CHAT_RESPONSE" | jq -r '.answer' | head -c 200
echo "..."
echo ""

# Check for enhanced features
echo "4. Verifying enhanced features..."

if echo "$CHAT_RESPONSE" | jq -e '.follow_up_questions' > /dev/null 2>&1; then
    echo "✅ Follow-up questions present"
    echo "$CHAT_RESPONSE" | jq -r '.follow_up_questions[]' | head -3
else
    echo "⚠️  Follow-up questions not found (may need book re-ingestion)"
fi
echo ""

if echo "$CHAT_RESPONSE" | jq -e '.retrieval_quality' > /dev/null 2>&1; then
    QUALITY=$(echo "$CHAT_RESPONSE" | jq -r '.retrieval_quality')
    echo "✅ Retrieval quality: $QUALITY"
else
    echo "⚠️  Retrieval quality not found"
fi
echo ""

if echo "$CHAT_RESPONSE" | jq -e '.sources[0].chapter_title' > /dev/null 2>&1; then
    echo "✅ Chapter/section metadata present in sources"
    echo "$CHAT_RESPONSE" | jq -r '.sources[0] | "Chapter: \(.chapter_title // "N/A"), Section: \(.section_title // "N/A")"'
else
    echo "⚠️  Chapter/section metadata not found (books need markdown re-ingestion)"
fi
echo ""

# API documentation
echo "5. Checking API documentation..."
DOCS_URL="https://$RAILWAY_URL/docs"
if curl -s -o /dev/null -w "%{http_code}" "$DOCS_URL" | grep -q "200"; then
    echo "✅ API docs accessible: $DOCS_URL"
else
    echo "⚠️  API docs not accessible"
fi
echo ""

echo "================================"
echo "✅ Deployment Verification Complete!"
echo "================================"
echo ""
echo "Next steps:"
echo "  1. Re-ingest books with markdown headers to populate metadata"
echo "  2. Monitor logs: railway logs --follow"
echo "  3. Update frontend to use: https://$RAILWAY_URL"
echo ""
