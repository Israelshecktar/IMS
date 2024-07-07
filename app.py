from flask import Flask, request, jsonify, url_for
from models import db, Inventory, User
from functools import wraps
from itsdangerous import URLSafeTimedSerializer
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
from flask_jwt_extended import (
    JWTManager,
    create_access_token,
    jwt_required,
    get_jwt_identity,
)
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

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
serializer = URLSafeTimedSerializer(app.config["JWT_SECRET_KEY"])


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
        if identity["role"] != "admin":
            return jsonify({"message": "Admins only!"}), 403
        return fn(*args, **kwargs)

    return wrapper


# Inventory Management Routes
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


@app.route("/inventory", methods=["GET"])
@jwt_required()
def get_inventory():
    query = Inventory.query

    # Search and filter parameters
    material = request.args.get("material")
    product_name = request.args.get("product_name")
    location = request.args.get("location")

    if material:
        query = query.filter(Inventory.material.ilike(f"%{material}%"))
    if product_name:
        query = query.filter(Inventory.product_name.ilike(f"%{product_name}%"))
    if location:
        query = query.filter(Inventory.location.ilike(f"%{location}%"))

    # Pagination parameters
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    inventory_items = pagination.items

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

    return jsonify(
        {
            "items": inventory_list,
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": pagination.page,
            "per_page": pagination.per_page,
        }
    )


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


@app.route("/inventory/below_threshold", methods=["GET"])
@jwt_required()
def get_inventory_below_threshold():
    threshold = 50
    low_inventory_items = Inventory.query.filter(
        Inventory.total_litres <= threshold
    ).all()
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
        for item in low_inventory_items
    ]
    return jsonify(inventory_list)


@app.route("/inventory/expiring_soon", methods=["GET"])
@jwt_required()
def get_inventory_expiring_soon():
    three_months_from_now = datetime.now() + timedelta(days=90)
    expiring_items = Inventory.query.filter(
        Inventory.best_before_date <= three_months_from_now
    ).all()
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
        for item in expiring_items
    ]
    return jsonify(inventory_list)


# User Management Routes
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


@app.route("/request_password_reset", methods=["POST"])
def request_password_reset():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    token = serializer.dumps(user.email, salt="password-reset-salt")
    reset_url = url_for("reset_password", token=token, _external=True)

    msg = Message("Password Reset Request", recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nPlease click the link to reset your password: {reset_url}"
    mail.send(msg)

    return jsonify({"message": "Password reset link sent to your email"}), 200


@app.route("/reset_password/<token>", methods=["POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except:
        return jsonify({"message": "The reset link is invalid or has expired."}), 400

    user = User.query.filter_by(email=email).first_or_404()
    data = request.get_json()
    user.set_password(data["password"])

    db.session.commit()

    # Send confirmation email
    msg = Message("Password Reset Successful", recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nYour password has been reset successfully."
    mail.send(msg)

    return jsonify({"message": "Password reset successfully"}), 200


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


@app.route("/update_profile", methods=["PUT"])
@jwt_required()
def update_profile():
    identity = get_jwt_identity()
    user = User.query.filter_by(username=identity["username"]).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    user.username = data.get("username", user.username)
    user.email = data.get("email", user.email)
    user.role = data.get("role", user.role)

    db.session.commit()

    # Send confirmation email
    msg = Message("Profile Update Successful", recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nYour profile has been updated successfully."
    mail.send(msg)

    return jsonify({"message": "Profile updated successfully"}), 200


# Reporting and Analytics Routes
@app.route("/report/inventory_levels", methods=["GET"])
@admin_required
def inventory_levels_report():
    inventory_items = Inventory.query.all()
    report = [
        {
            "product_name": item.product_name,
            "total_litres": item.total_litres,
            "location": item.location,
        }
        for item in inventory_items
    ]
    return jsonify(report)


@app.route("/report/user_activity", methods=["GET"])
@admin_required
def user_activity_report():
    users = User.query.all()
    report = [
        {
            "username": user.username,
            "email": user.email,
            "role": user.role,
            "last_login": user.last_login.isoformat() if user.last_login else None,
        }
        for user in users
    ]
    return jsonify(report)


# Automated Email Notifications
def check_inventory_levels():
    low_inventory_items = Inventory.query.filter(Inventory.total_litres < 50).all()
    if low_inventory_items:
        product_list = "\n".join(
            [
                f"{item.product_name}: {item.total_litres} liters"
                for item in low_inventory_items
            ]
        )
        msg = Message("Low Inventory Alert", recipients=[MAIL_USERNAME])
        msg.body = f"The following products are below the 50 liters threshold:\n\n{product_list}"
        mail.send(msg)


def check_expiring_products():
    three_months_from_now = datetime.now() + timedelta(days=90)
    expiring_items = Inventory.query.filter(
        Inventory.best_before_date <= three_months_from_now
    ).all()
    if expiring_items:
        product_list = "\n".join(
            [
                f"{item.product_name}: expires on {item.best_before_date}"
                for item in expiring_items
            ]
        )
        msg = Message("Expiration Notice", recipients=[MAIL_USERNAME])
        msg.body = f"The following products are expiring within the next 3 months:\n\n{product_list}"
        mail.send(msg)


# Scheduling the Tasks
scheduler = BackgroundScheduler()
scheduler.add_job(
    func=check_inventory_levels, trigger="interval", hours=24
)  # Check daily
scheduler.add_job(
    func=check_expiring_products, trigger="interval", weeks=1
)  # Check weekly
scheduler.start()

# Initialize the database
with app.app_context():
    db.create_all()

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
