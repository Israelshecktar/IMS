from models import db, Inventory
from app import app


# Function to clear the inventory table
def clear_inventory():
    with app.app_context():
        db.session.query(Inventory).delete()
        db.session.commit()


# Call the function to clear the inventory table
clear_inventory()
