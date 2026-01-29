#!/bin/bash

echo "------------------------------------------------"
echo "🛡️  FLIPTRYBE 2026: PRODUCTION SIMULATION"
echo "------------------------------------------------"

# 1. Activate Environment
source venv/bin/activate

# 2. Install Production Server (Gunicorn)
if ! pip show gunicorn > /dev/null; then
    echo "📦 Installing Gunicorn..."
    pip install gunicorn
fi

# 3. Set Environment to Production
export FLASK_DEBUG=False
echo "✅ Debug Mode: OFF"

# 4. Run with Gunicorn (4 Worker Processes)
echo "🚀 Launching Green Unicorn (Gunicorn) Server..."
echo "------------------------------------------------"
echo "   Access the Grid at: http://127.0.0.1:8000"
echo "   Press Ctrl+C to shut down."
echo "------------------------------------------------"

# Syntax: gunicorn [entry_file]:[app_variable]
gunicorn -w 4 -b 127.0.0.1:8000 run:app