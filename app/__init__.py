import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate
from config import Config
from app.celery_utils import make_celery, init_celery_config

# --- 🛰️ 1. GLOBAL INFRASTRUCTURE NODES ---
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'
migrate = Migrate()
celery = None # Initialized via factory

def create_app(config_class=Config):
    """
    The Application Factory: Synchronizes all nodes and starts the ignition sequence.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)

    @app.before_request
    def api_only_guard():
        path = request.path or ""
        if path.startswith("/api/") or path in ("/api/health", "/health"):
            return None
        if path.startswith("/static/"):
            return None
        if path == "/admin/escrow/run":
            return None
        if path in ("/listings", "/shortlets", "/declutter"):
            return None
        if path == "/":
            return jsonify({
                "status": "ok",
                "service": "api",
                "message": "FlipTrybe API-only service. Frontend is deployed separately."
            }), 200
        return jsonify({
            "status": "error",
            "message": "API-only service. Use /api/* endpoints."
        }), 404

    # --- 🧬 2. DATABASE & SESSION SYNC ---
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)

    # --- 🚁 3. BACKGROUND SIGNAL ENGINE (CELERY) ---
    init_celery_config(app)
    global celery
    celery = make_celery(app)

    # --- 📜 4. LOGGER NODE SYNCHRONIZATION ---
    # Audit: Ensuring contact with /logs/fliptrybe.log
    if not app.debug and not app.testing:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Rotating file handler: 10MB limit per file, keeping 10 logs max
        file_handler = RotatingFileHandler('logs/fliptrybe.log', 
                                           maxBytes=10240000, 
                                           backupCount=10)
        
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)

        app.logger.setLevel(logging.INFO)
        app.logger.info('🛰️  FlipTrybe Grid Startup Signal: Active')

    # --- 🛡️ 5. BLUEPRINT REGISTRY (ROUTING HANDSHAKE) ---
    from app.main import main as main_blueprint
    from app.auth import auth as auth_blueprint
    from app.admin import admin as admin_blueprint
    from app.api import api as api_blueprint, list_listings, list_shortlets, list_declutter
    
    # Synchronizing routes with the central core
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(api_blueprint, url_prefix='/api')
    app.add_url_rule("/listings", endpoint="public_listings", view_func=list_listings)
    app.add_url_rule("/shortlets", endpoint="public_shortlets", view_func=list_shortlets)
    app.add_url_rule("/declutter", endpoint="public_declutter", view_func=list_declutter)

    # --- Minimal health endpoints (no auth, no DB) ---
    @app.get("/api/health")
    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    return app, celery
