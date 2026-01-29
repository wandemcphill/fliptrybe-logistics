import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_bcrypt import Bcrypt
from celery import Celery

# 1. Initialize extensions globally
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

# 🟢 INITIALIZE CELERY GLOBALLY: Prevents worker startup crashes
celery = Celery(__name__)

def create_app():
    app = Flask(__name__)
    
    # 🔐 PRODUCTION CONFIGURATION
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dev-key-123'
    
    # --- 💾 DATABASE ROUTING ---
    db_url = os.environ.get('DATABASE_URL')
    
    # Force Postgres to use the psycopg2 driver
    if db_url:
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql+psycopg2://", 1)
        elif db_url.startswith("postgresql://"):
            db_url = db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    
    # Fallback to Persistent Disk (SQLite) if no Postgres is found
    if os.environ.get('RENDER') and not db_url:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////var/lib/data/fliptrybe.db'
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = db_url or 'sqlite:///fliptrybe.db'
    
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # --- ⚡ REDIS & CELERY ---
    redis_url = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    app.config['CELERY_BROKER_URL'] = redis_url
    app.config['CELERY_RESULT_BACKEND'] = redis_url

    # 2. Bind extensions to app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # 3. Synchronize Celery with App Config
    celery.conf.update(app.config)
    
    # Bridging: Allows tasks to use the Database context
    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)
    celery.Task = ContextTask

    # 4. Register Blueprints
    from app.main import main
    from app.auth import auth
    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app