import os
from app import create_app, db
from sqlalchemy import text

app, celery = create_app()

def diagnostic():
    print("🔍 INITIATING GRID HEALTH CHECK...")
    with app.app_context():
        # 1. Database Check
        try:
            db.session.execute(text('SELECT 1'))
            print("✅ VAULT: PostgreSQL Connection Secured.")
        except Exception as e:
            print(f"❌ VAULT: Connection Failed - {e}")

        # 2. Cache Check
        try:
            from redis import Redis
            redis = Redis.from_url(app.config['REDIS_URL'])
            redis.ping()
            print("✅ CACHE: Redis Signal Active.")
        except Exception as e:
            print(f"❌ CACHE: Redis Disconnected - {e}")

        # 3. Environment Check
        keys = ['PAYSTACK_SECRET_KEY', 'TERMII_API_KEY']
        for key in keys:
            if os.environ.get(key):
                print(f"✅ SIGNAL: {key} loaded.")
            else:
                print(f"⚠️  SIGNAL: {key} MISSING in Environment.")

diagnostic()