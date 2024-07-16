from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


# Define the User model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(225), nullable=False)
    role = db.Column(db.Enum("admin", "management", "staff"), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# Define the Inventory model
class Inventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    material = db.Column(db.Numeric(15), unique=True, nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    total_litres = db.Column(db.Numeric(10, 2), nullable=False)
    date_received = db.Column(db.Date, nullable=False)
    best_before_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(255), nullable=False)


# define inventory transaction model
class InventoryTransaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id"), nullable=False)
    quantity_taken = db.Column(db.Numeric(10, 2), nullable=False)
    date_taken = db.Column(db.DateTime, default=datetime.utcnow)
    inventory = db.relationship(
        "Inventory", backref=db.backref("transactions", lazy=True)
    )


# define deleted inventory model
class DeletedInventory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    original_id = db.Column(db.Integer, nullable=False)
    material = db.Column(db.Numeric(15), nullable=False)
    product_name = db.Column(db.String(255), nullable=False)
    total_litres = db.Column(db.Numeric(10, 2), nullable=False)
    date_received = db.Column(db.Date, nullable=False)
    best_before_date = db.Column(db.Date, nullable=False)
    location = db.Column(db.String(255), nullable=False)
    date_deleted = db.Column(db.DateTime, default=datetime.utcnow)
