import os
from app import create_app, db
from app.models import User, Listing, Order, Transaction, Notification, PriceHistory

# Initialize the synchronized core
app, celery = create_app()

if __name__ == '__main__':
    # Standard local ignition on Port 5000
    app.run(host='0.0.0.0', port=5000, debug=True)