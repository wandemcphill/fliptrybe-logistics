import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

load_dotenv()
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
csrf = CSRFProtect()

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fliptrybe-vault-2026')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///fliptrybe_v11.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    from app.auth import auth
    from app.main import main
    from app.admin import admin
    app.register_blueprint(auth)
    app.register_blueprint(main)
    app.register_blueprint(admin)

    @app.context_processor
    def inject_global_signals():
        return {
            'activity_signals': [
                {'type': 'handshake', 'msg': 'Escrow Handshake: Lagos Hub'},
                {'type': 'market', 'msg': 'New Listing: iPhone 15 Pro Max'},
                {'type': 'handshake', 'msg': 'Verified Seller: PrimeVendor Online'}
            ]
        }

    return app