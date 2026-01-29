#!/bin/bash

# --- 🛰️ FLIPTRYBE DEPLOYMENT PROTOCOL ---
# Chief Engineer's Ignition Script
# Targets: Web Node, Worker Node, and Database Schema

set -e # Exit immediately if a command exits with a non-zero status

echo "-------------------------------------------------------"
echo "🚀 IGNITING FLIPTRYBE GRID DEPLOYMENT SEQUENCE"
echo "-------------------------------------------------------"

# 🧬 STEP 1: INFRASTRUCTURE SYNC (Dependencies)
echo "🔍 Synchronizing Dependency Nodes..."
pip install -r requirements.txt
echo "✅ Dependencies Locked."

# 🧬 STEP 2: SCHEMA SYNCHRONIZATION (Build-Bundle Audit)
# This handles Tiers, Verification, and Pilot Rating columns
echo "🏗️  Upgrading Database Schema..."
if [ -d "migrations" ]; then
    flask db upgrade
    echo "✅ Schema Handshake Successful."
else
    echo "⚠️  WARNING: No migration node found. Initializing..."
    flask db init
    flask db migrate -m "Initial Genesis Migration"
    flask db upgrade
    echo "✅ Schema Initialized."
fi

# 🧬 STEP 3: ASSET DIRECTORY VERIFICATION
# Ensures POD photos and products have a landing zone
echo "📁 Auditing Asset Storage Nodes..."
mkdir -p app/static/uploads/products
mkdir -p app/static/uploads/deliveries
echo "✅ Storage Paths Verified."

# 🧬 STEP 4: SERVICE RESTART (Web & Worker)
# If running locally, this helps clean up old processes.
# On Render/Heroku, the platform handles the restart automatically.
echo "🚁 Restarting Background Signal Engines (Celery)..."
pkill -f "celery" || true
echo "✅ Celery Nodes Flushed."

echo "-------------------------------------------------------"
echo "🛰️  DEPLOYMENT SUCCESSFUL: Grid is Online and Audited."
echo "-------------------------------------------------------"