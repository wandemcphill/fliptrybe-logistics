import os
import sys
from app import create_app, db

# 🌐 Load Environment Variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# This 'app' object is what Gunicorn looks for in your Procfile (run:app)
app = create_app()

def bootstrap_system():
    """
    Automated System Check: Ensures folders and database are ready.
    """
    print("\n🚀 [FLIPTRYBE] INITIALIZING PROTOCOL...")
    
    # 📁 Ensure Upload Directories Exist
    upload_path = app.config.get('UPLOAD_FOLDER', os.path.join(app.root_path, 'static/uploads'))
    subfolders = ['kyc', 'product', 'disputes']
    
    for folder in subfolders:
        full_path = os.path.join(upload_path, folder)
        if not os.path.exists(full_path):
            print(f"📁 Creating secure storage hub: {full_path}")
            os.makedirs(full_path, exist_ok=True)

    # 🛠️ Database Health Check
    try:
        with app.app_context():
            from app.models import User
            User.query.limit(1).all()
        print("✅ DATABASE: Connection Stable.")
    except Exception:
        print("⚠️  DATABASE: Signal Weak. Run 'python -m flask db upgrade' or 'python seed_all.py'")

# Logic for Local Development Execution
if __name__ == '__main__':
    bootstrap_system()
    
    # Cloud providers like Render/Heroku inject a 'PORT' environment variable
    PORT = int(os.environ.get('PORT', 5000))
    # Standard production security: Default to False if not explicitly 'True'
    DEBUG = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"📡 TERMINAL ACTIVE: http://0.0.0.0:{PORT}")
    print(f"🛠️  MODE: {'DEVELOPMENT' if DEBUG else 'PRODUCTION'}\n")
    
    app.run(
        host='0.0.0.0', 
        port=PORT, 
        debug=DEBUG
    )