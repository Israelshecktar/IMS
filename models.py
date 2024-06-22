from app import db
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

class User(db.Model):
    __tablename__ = "users"
    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)

    def __repr__(self):
        return f"<User(username='{self.username}', email='{self.email}')>"


class Category(db.Model):
    __tablename__ = "categories"
    category_id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(50), unique=True, nullable=False)

    materials = db.relationship(
        "Material", back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Category(category_name='{self.category_name}')>"


class Material(db.Model):
    __tablename__ = "materials_inventory"
    material_id = db.Column(db.Integer, primary_key=True)
    material_name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(
        db.Integer, db.ForeignKey("categories.category_id"), nullable=False
    )
    current_quantity = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    description = db.Column(db.String(255), nullable=True)

    category = db.relationship("Category", back_populates="materials")

    def __repr__(self):
        return f"<Material(material_name='{self.material_name}', current_quantity={self.current_quantity})>"
