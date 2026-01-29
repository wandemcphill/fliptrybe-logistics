import os

# Get the absolute path of the directory where this file (config.py) is located
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-key-for-local-grid'
    
    # FORCED SYNC: This joins the absolute path with the instance folder
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'instance', 'fliptrybe.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Other configs remain the same...
    CELERY_BROKER_URL = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'
    RESULT_BACKEND = os.environ.get('REDIS_URL') or 'redis://localhost:6379/0'