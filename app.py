from flask import Flask, request, jsonify
from models import db, Inventory, User
from functools import wraps
from config import (
    SQLALCHEMY_DATABASE_URI,
    JWT_SECRET_KEY,
    MAIL_SERVER,
    MAIL_PORT,
    MAIL_USE_TLS,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER,
)
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["JWT_SECRET_KEY"] = JWT_SECRET_KEY
app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USE_TLS"] = MAIL_USE_TLS
app.config["MAIL_USERNAME"] = MAIL_USERNAME
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD
app.config["MAIL_DEFAULT_SENDER"] = MAIL_DEFAULT_SENDER

mail = Mail(app)
jwt = JWTManager(app)
db.init_app(app)

# Home Route
@app.route("/")
def home():
    return "Hello Shecktar!, your app is running and connected to the stockguard db"

# Role-based access control decorator
def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        identity = get_jwt_identity()
        if identity['role'] != 'admin':
            return jsonify({"message": "Admins only!"}), 403
        return fn(*args, **kwargs)
    return wrapper

# Route to add an inventory item
@app.route("/add_inventory", methods=["POST"])
@admin_required
def add_inventory():
    data = request.get_json()
    try:
        new_inventory = Inventory(
            material=data["material"],
            product_name=data["product_name"],
            total_litres=data["total_litres"],
            date_received=data["date_received"],
            best_before_date=data["best_before_date"],
            location=data["location"],
        )
        db.session.add(new_inventory)
        db.session.commit()
        return jsonify({"message": "Inventory item added successfully"}), 201
    except KeyError as e:
        return jsonify({"error": f"Missing field: {e.args[0]}"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Route to get all inventory items
@app.route("/inventory", methods=["GET"])
@jwt_required()
def get_inventory():
    inventory_items = Inventory.query.all()
    inventory_list = [
        {
            "id": item.id,
            "material": item.material,
            "product_name": item.product_name,
            "total_litres": item.total_litres,
            "date_received": item.date_received.isoformat(),
            "best_before_date": item.best_before_date.isoformat(),
            "location": item.location,
        }
        for item in inventory_items
    ]
    return jsonify(inventory_list)

# Route to get the names of HEMPEL products in stock
@app.route("/hempel_products", methods=["GET"])
@jwt_required()
def get_hempel_products():
    hempel_products = Inventory.query.with_entities(Inventory.product_name).all()
    product_names = [product.product_name for product in hempel_products]
    return jsonify(product_names)

@app.route("/update_inventory/<int:id>", methods=["PUT"])
@admin_required
def update_inventory(id):
    data = request.get_json()
    inventory_item = Inventory.query.get(id)
    if not inventory_item:
        return jsonify({"message": "Inventory item not found"}), 404

    inventory_item.material = data.get("material", inventory_item.material)
    inventory_item.product_name = data.get("product_name", inventory_item.product_name)
    inventory_item.total_litres = data.get("total_litres", inventory_item.total_litres)
    inventory_item.date_received = data.get(
        "date_received", inventory_item.date_received
    )
    inventory_item.best_before_date = data.get(
        "best_before_date", inventory_item.best_before_date
    )
    inventory_item.location = data.get("location", inventory_item.location)

    db.session.commit()
    return jsonify({"message": "Inventory item updated successfully"}), 200

@app.route("/delete_inventory/<int:id>", methods=["DELETE"])
@admin_required
def delete_inventory(id):
    inventory_item = Inventory.query.get(id)
    if not inventory_item:
        return jsonify({"message": "Inventory item not found"}), 404

    db.session.delete(inventory_item)
    db.session.commit()
    return jsonify({"message": "Inventory item deleted successfully"}), 200

# Route to register a new user
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    existing_user = User.query.filter(
        (User.username == data["username"]) | (User.email == data["email"])
    ).first()
    if existing_user:
        return jsonify({"message": "Username or email already exists"}), 400

    new_user = User(username=data["username"], email=data["email"], role=data["role"])
    new_user.set_password(data["password"])
    db.session.add(new_user)
    db.session.commit()

    # Send email notification
    msg = Message("Welcome to StockGuard", recipients=[new_user.email])
    msg.body = f"Hello {new_user.username},\n\nThank you for registering at StockGuard. Your account has been successfully created."
    mail.send(msg)

    return jsonify({"message": "User registered successfully"}), 201

@app.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    if user and user.check_password(data["password"]):
        access_token = create_access_token(
            identity={"username": user.username, "role": user.role}
        )
        return jsonify(access_token=access_token), 200
    return jsonify({"message": "Invalid credentials"}), 401

# Initialize the database
with app.app_context():
    db.create_all()

# Run the Flask app
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
