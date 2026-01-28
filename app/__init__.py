import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# ==========================================
# 🔐 LOAD ENVIRONMENT VAULT
# ==========================================
load_dotenv()

# ==========================================
# 🏗️ GLOBAL EXTENSIONS
# ==========================================
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
migrate = Migrate()
csrf = CSRFProtect()

# Login Configuration (The Guardian)
login_manager.login_view = 'auth.login'
login_manager.login_message = "Please access your terminal to proceed."
login_manager.login_message_category = "error"

def create_app():
    app = Flask(__name__)

    # ==========================================
    # ⚙️ CORE CONFIGURATION (2026 Standards)
    # ==========================================
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fliptrybe-ultra-secure-key-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fliptrybe_v6.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # File Storage Strategy (KYC & Dispute Evidence)
    app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 # 16MB Armor

    # 💳 PAYSTACK TRANSMISSION KEYS
    app.config['PAYSTACK_PUBLIC_KEY'] = os.environ.get('PAYSTACK_PUBLIC_KEY')
    app.config['PAYSTACK_SECRET_KEY'] = os.environ.get('PAYSTACK_SECRET_KEY')

    # 📱 TERMII SMS/WHATSAPP KEYS
    app.config['TERMII_API_KEY'] = os.environ.get('TERMII_API_KEY')
    app.config['TERMII_SENDER_ID'] = os.environ.get('TERMII_SENDER_ID', 'FlipTrybe')

    # ==========================================
    # 🔌 INITIALIZE PLUGINS
    # ==========================================
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # ==========================================
    # 🕵️‍♂️ USER LOADER (This was missing!)
    # ==========================================
    @login_manager.user_loader
    def load_user(user_id):
        # We import here to avoid "Circular Import" errors
        from app.models import User
        return User.query.get(int(user_id))

    # ==========================================
    # 🔗 BLUEPRINT REGISTRATION
    # ==========================================
    from app.auth import auth as auth_blueprint
    from app.main import main as main_blueprint
    from app.admin import admin as admin_blueprint 

    app.register_blueprint(auth_blueprint)
    app.register_blueprint(main_blueprint)
    app.register_blueprint(admin_blueprint)

    # ==========================================
    # 📥 TEMPLATE CONTEXT PROCESSORS
    # ==========================================
    @app.context_processor
    def inject_global_vars():
        """Broadcasts system variables to all UI nodes."""
        return {
            'paystack_public_key': app.config['PAYSTACK_PUBLIC_KEY'],
            'app_name': 'FlipTrybe'
        }

    # ==========================================
    # 📓 SYSTEM LOGGING (The Black Box)
    # ==========================================
    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/fliptrybe.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('FlipTrybe Core Startup Initiated')

    # ==========================================
    # 🛠️ DATABASE SYNC
    # ==========================================
    with app.app_context():
        db.create_all()

    return app