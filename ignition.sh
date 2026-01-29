#!/bin/bash

# --- 🛰️ FLIPTRYBE IGNITION PROTOCOL ---
# Chief Engineer's Parallel Execution Engine
# Synchronizing Web Node, Signal Worker, and Heartbeat

# 🛡️ 1. ENVIRONMENT AUDIT
echo "🔍 Performing Pre-Flight Environment Audit..."
if [ ! -f .env ]; then
    echo "❌ CRITICAL FAILURE: .env file not detected. Ignition aborted."
    exit 1
fi

# Load variables for internal checks
export $(grep -v '^#' .env | xargs)

# 🧬 2. INFRASTRUCTURE PING (Redis/Database)
echo "📡 Checking Signal Infrastructure (Redis)..."
# Check if Redis is reachable before spinning up Celery
if ! command -v redis-cli &> /dev/null; then
    echo "⚠️  WARNING: redis-cli not found. Skipping hardware ping."
else
    if redis-cli ping | grep -q PONG; then
        echo "✅ Redis Node: Optimal."
    else
        echo "❌ CRITICAL: Redis Node Offline. Handshake Pulse will fail."
        exit 1
    fi
fi

# 🏗️ 3. PROCESS SYNCHRONIZATION
# We use an '&' to run processes in the background and 'wait' to manage them.

cleanup() {
    echo ""
    echo "🛑 SIGNAL RECEIVED: Engaging Emergency Shutdown..."
    kill $(jobs -p)
    echo "✅ Grid nodes deactivated."
    exit
}

# Trap SIGINT (Ctrl+C) to ensure we don't leave zombie processes
trap cleanup SIGINT

echo "-------------------------------------------------------"
echo "🚀 GRID IGNITION: Spinning up FlipTrybe Nodes"
echo "-------------------------------------------------------"

# NODE 1: THE WEB ENGINE
echo "🛰️  Starting Web Engine (Flask)..."
python run.py & 
WEB_PID=$!

# NODE 2: THE SIGNAL WORKER (Celery)
# We wait 2 seconds to ensure the Flask App Context is mapped first
sleep 2
echo "🚁 Starting Signal Worker (Celery)..."
celery -A run.celery worker --loglevel=info &
WORKER_PID=$!

# NODE 3: THE DASHBOARD REFRESH (Optional/Local dev only)
# If you have a flower dashboard for monitoring tasks
# celery -A run.celery flower &

echo "-------------------------------------------------------"
echo "✅ FLIPTRYBE ONLINE: All nodes are synchronized."
echo "🔗 Local Access: http://localhost:5000"
echo "🛠️  Admin Terminal: http://localhost:5000/admin/vault-control"
echo "-------------------------------------------------------"

# Keep the script alive so it can manage the background processes
wait