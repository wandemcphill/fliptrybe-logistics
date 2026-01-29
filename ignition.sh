#!/bin/bash

echo "------------------------------------------------"
echo "🚀 FLIPTRYBE 2026: IGNITION SEQUENCE"
echo "------------------------------------------------"

# 1. Check for Virtual Environment
if [ -d "venv" ]; then
    echo "✅ Virtual Environment found. Activating..."
    source venv/bin/activate
else
    echo "⚙️  Creating new Virtual Environment..."
    python3 -m venv venv
    source venv/bin/activate
fi

# 2. Install Dependencies
echo "📦 Synchronizing Dependencies..."
pip install -r requirements.txt

# 3. Check for Database
if [ ! -f "app/site.db" ]; then
    echo "⚠️  Database missing. Running Seed Script..."
    python seed_all.py
else
    echo "✅ Database found. Skipping seed."
fi

# 4. Launch Server
echo "------------------------------------------------"
echo "📡 STARTING DEVELOPMENT SERVER (Port 5000)"
echo "------------------------------------------------"
python run.py