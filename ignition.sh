#!/bin/bash

echo "🛰️ FLIPTRYBE 2026: INITIALIZING SOVEREIGN DEPLOYMENT..."

# 1. Construct Physical Asset Nodes
echo "📂 Constructing static signal hubs..."
mkdir -p app/static/uploads/kyc
mkdir -p app/static/uploads/product
mkdir -p app/static/uploads/disputes

# 2. Database Synchronization
echo "🗄️ Synchronizing fliptrybe_v6.db..."
if [ ! -d "migrations" ]; then
    flask db init
fi

flask db migrate -m "Ignition: Sovereign Core v6"
flask db upgrade

# 3. Final Pulse
echo "🏁 DEPLOYMENT INITIALIZED. RUN 'python run.py' TO IGNITE."