#!/bin/bash

echo "🛰️  FLIPTRYBE 2026: SECURING REPOSITORY..."

# 1. Initialize Git if not already present
if [ ! -d ".git" ]; then
    git init
    echo "✅ Git Repository Initialized."
fi

# 2. Hard-check for .gitignore to prevent signal leaks
if [ ! -f ".gitignore" ]; then
    echo "⚠️  CRITICAL: .gitignore missing. Creating security barrier..."
    echo ".env" >> .gitignore
    echo "instance/" >> .gitignore
    echo "venv/" >> .gitignore
    echo "__pycache__/" >> .gitignore
    echo "*.db" >> .gitignore
    echo "app/static/uploads/*" >> .gitignore
    echo "!app/static/uploads/.gitkeep" >> .gitignore
fi

# 3. Handle Static Asset Persistence (The Placeholder Strategy)
echo "📁 Locking storage nodes..."
touch app/static/uploads/kyc/.gitkeep
touch app/static/uploads/product/.gitkeep
touch app/static/uploads/disputes/.gitkeep

# 4. Stage and Commit
git add .
git commit -m "🚀 FlipTrybe v1.0: Sovereign Marketplace Initialized"

# 5. Instructions for the final push
echo ""
echo "🏁 REPOSITORY ARMED. FINAL STEPS:"
echo "1. Create a new repository on GitHub/GitLab."
echo "2. Run: git remote add origin <your_repository_url>"
echo "3. Run: git branch -M main"
echo "4. Run: git push -u origin main"
echo ""
echo "✅ Operational Readiness: 100%"