from flask import Flask
from flask_login import LoginManager
# 🛑 FIX: Import the EXISTING db from models, don't create a new one!
from .models import db 

def create_app():
    app = Flask(__name__)

    # 🔐 CONFIGURATION
    app.config['SECRET_KEY'] = 'fliptrybe-secret-key-998877' 
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///fliptrybe_v5.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize the db from models.py
    db.init_app(app)

    # 👤 LOGIN MANAGER
    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = "Please log in to access this page."
    login_manager.login_message_category = "error"
    login_manager.init_app(app)

    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 🔌 BLUEPRINTS
    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Create DB Tables if they don't exist
    with app.app_context():
        db.create_all()

    return app