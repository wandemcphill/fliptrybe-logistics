import os
import sys
from app import create_app, db, celery

def run_diagnostics():
    app = create_app()
    with app.app_context():
        print("\n" + "🔍" + " ="*25)
        print(" FLIPTRYBE GRID: SYSTEM DIAGNOSTICS")
        print(" ="*25 + "\n")

        # 1. Database Check (PostgreSQL)
        print("[1/3] 💾 Testing Database Vault...")
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            print("      -> STATUS: ONLINE (Postgres Connection Stable)")
        except Exception as e:
            print(f"      -> STATUS: CRITICAL ERROR: {e}")

        # 2. Redis Synapse Check
        print("\n[2/3] ⚡ Testing Redis Synapse...")
        try:
            import redis
            r = redis.from_url(app.config['CELERY_BROKER_URL'])
            r.ping()
            print("      -> STATUS: ONLINE (Redis Broker Responsive)")
        except Exception as e:
            print(f"      -> STATUS: DISCONNECTED: {e}")

        # 3. Celery Worker Heartbeat
        print("\n[3/3] ⚙️  Probing Worker Nodes...")
        try:
            inspect = celery.control.inspect()
            active = inspect.active()
            if active:
                for node, tasks in active.items():
                    print(f"      -> STATUS: OPTIMAL (Worker Node '{node}' is Active)")
            else:
                print("      -> STATUS: OFFLINE (No Workers Found in Synapse)")
        except Exception as e:
            print(f"      -> STATUS: SIGNAL FAILED: {e}")

        print("\n" + "="*52)
        print(" DIAGNOSTICS COMPLETE")
        print("="*52 + "\n")

if __name__ == "__main__":
    run_diagnostics()