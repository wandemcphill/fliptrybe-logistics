from app import create_app

# The Flask CLI only wants the 'app' object, so we extract it here
app, celery = create_app()

# This is the secret handshake for the Flask CLI
application = app