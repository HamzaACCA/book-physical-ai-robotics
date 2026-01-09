#!/bin/bash
# Quick Railway Deployment Script

echo "🚀 Railway Deployment Helper"
echo "=============================="
echo ""

# Check if logged in
echo "1. Checking Railway login status..."
if ! railway whoami &> /dev/null; then
    echo "❌ Not logged in to Railway"
    echo "   Run: railway login"
    echo ""
    echo "   This will open your browser for authentication."
    exit 1
else
    echo "✅ Logged in to Railway"
fi

# Check git status
echo ""
echo "2. Checking git status..."
if [[ -n $(git status -s) ]]; then
    echo "⚠️  Uncommitted changes detected"
    echo "   Commit changes first or they won't be deployed"
    exit 1
else
    echo "✅ Git working tree clean"
fi

# Check branch
echo ""
echo "3. Checking current branch..."
CURRENT_BRANCH=$(git branch --show-current)
if [[ "$CURRENT_BRANCH" != "backend" ]]; then
    echo "⚠️  Not on 'backend' branch (currently on: $CURRENT_BRANCH)"
    echo "   Switch to backend branch: git checkout backend"
    exit 1
else
    echo "✅ On 'backend' branch"
fi

# Check Railway link
echo ""
echo "4. Checking Railway project link..."
if ! railway status &> /dev/null; then
    echo "❌ Not linked to a Railway project"
    echo ""
    echo "   Choose one:"
    echo "   - Link existing: railway link"
    echo "   - Create new: railway init"
    exit 1
else
    echo "✅ Linked to Railway project"
    railway status
fi

# Confirm deployment
echo ""
echo "5. Ready to deploy!"
echo ""
read -p "Deploy to Railway now? (y/N) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled"
    exit 0
fi

# Deploy
echo ""
echo "🚀 Deploying to Railway..."
railway up

echo ""
echo "✅ Deployment initiated!"
echo ""
echo "Next steps:"
echo "1. Monitor logs: railway logs"
echo "2. Check status: railway status"
echo "3. Open app: railway open"
echo "4. Test health: curl \$(railway status --json | jq -r '.domain')/health"
