import os

# Get the absolute path for local SQLite usage
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    # --- 🛰️ 1. SECURITY NODES ---
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-local-grid'

    # --- 🧬 2. DATABASE HANDSHAKE (PROD vs LOCAL) ---
    uri = os.environ.get('DATABASE_URL')
    
    if uri:
        # Render/PostgreSQL Sync: Fixes the 'postgres://' vs 'postgresql://' quirk
        if uri.startswith("postgres://"):
            uri = uri.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = uri
    else:
        # Localhost/SQLite Sync: Uses absolute path to 'instance/'
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'fliptrybe.db')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- 🚁 3. BACKGROUND SIGNAL ENGINE ---
    CELERY_BROKER_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    RESULT_BACKEND = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'

    # --- 💳 4. FINANCIAL & SMS GATEWAYS ---
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
    TERMII_API_KEY = os.environ.get('TERMII_API_KEY')
    TERMII_SENDER_ID = os.environ.get('TERMII_SENDER_ID', 'FlipTrybe')