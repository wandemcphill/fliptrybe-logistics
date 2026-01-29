import os
from celery import Celery

# --- 🛰️ 1. THE CELERY FACTORY (Infrastructure Node) ---

def make_celery(app):
    """
    Builds the Celery instance and synchronizes it with the Flask context.
    This ensures background tasks can talk to the Database (SQLAlchemy).
    """
    # Initialize Celery with Redis/RabbitMQ broker from environment
    celery = Celery(
        app.import_name,
        backend=app.config.get('CELERY_RESULT_BACKEND'),
        broker=app.config.get('CELERY_BROKER_URL')
    )
    
    # Inject application configuration into Celery
    celery.conf.update(app.config)

    # --- 🛡️ THE CONTEXT WRAPPER ---
    class ContextTask(celery.Task):
        """
        Structural Sync: Every task executed by the worker will automatically 
        wrap itself in a Flask 'app_context'. This allows tasks to use db.session 
        without crashing.
        """
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery

# --- ⚙️ 2. CELERY CONFIGURATION PROTCOLS ---

def init_celery_config(app):
    """
    Build-Bundle Audit: Standardizing background signal paths.
    Ensures Redis is used for high-frequency Nigerians SMS signals.
    """
    app.config.update(
        CELERY_BROKER_URL=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        CELERY_RESULT_BACKEND=os.environ.get('REDIS_URL', 'redis://localhost:6379/0'),
        CELERY_TASK_SERIALIZER='json',
        CELERY_ACCEPT_CONTENT=['json'],
        CELERY_RESULT_SERIALIZER='json',
        CELERY_TIMEZONE='Africa/Lagos',
        CELERY_ENABLE_UTC=True,
        # Critical for Build #5: Prevents tasks from blocking the worker
        CELERYD_PREFETCH_MULTIPLIER=1,
        CELERY_TASK_SOFT_TIME_LIMIT=60, # 1 minute max per signal
    )

# --- 📜 3. TASK REGISTRY LOGIC ---
# Note: Tasks are defined in utils.py to maintain the "Central Nervous System"
# but they are discovered by the worker via this engine.