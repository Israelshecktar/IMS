from flask import Flask, request, jsonify, url_for, send_file, send_from_directory
import io
import pandas as pd
from models import db, Inventory, User, InventoryTransaction
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
from auth_routes import auth_bp
from frontend_routes import frontend_bp

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

# Register the frontend blueprint first
app.register_blueprint(frontend_bp)

# Register the blueprint
app.register_blueprint(auth_bp, url_prefix="/auth")


# inventory management routes
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


@app.route("/take_inventory", methods=["POST"])
@jwt_required()
def take_inventory():
    data = request.get_json()
    inventory_item = Inventory.query.get(data["id"])

    if not inventory_item:
        return jsonify({"message": "Inventory item not found"}), 404

    quantity_to_take = data.get("quantity", 0)

    if quantity_to_take <= 0:
        return jsonify({"message": "Invalid quantity"}), 400

    if inventory_item.total_litres < quantity_to_take:
        return jsonify({"message": "Insufficient inventory"}), 400

    inventory_item.total_litres -= quantity_to_take

    # Log the transaction
    transaction = InventoryTransaction(
        inventory_id=inventory_item.id, quantity_taken=quantity_to_take
    )
    db.session.add(transaction)
    db.session.commit()

    return (
        jsonify(
            {
                "message": "Inventory updated successfully",
                "remaining_quantity": inventory_item.total_litres,
            }
        ),
        200,
    )


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

    if request.args.get("download") == "true":
        # Create a DataFrame
        df = pd.DataFrame(inventory_list)

        # Save to a BytesIO object
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Low Inventory")
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="low_inventory_report.xlsx",
        )

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

    if request.args.get("download") == "true":
        # Create a DataFrame
        df = pd.DataFrame(inventory_list)

        # Save to a BytesIO object
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Expiring Soon")
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="expiring_soon_report.xlsx",
        )

    return jsonify(inventory_list)


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

    if request.args.get("download") == "true":
        # Create a DataFrame
        df = pd.DataFrame(report)

        # Save to a BytesIO object
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventory Levels")
        output.seek(0)

        return send_file(
            output, as_attachment=True, download_name="inventory_levels_report.xlsx"
        )

    return jsonify(report)


@app.route("/report/inventory_taken", methods=["GET"])
@admin_required
def inventory_taken_report():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return jsonify({"message": "Please provide both start_date and end_date"}), 400

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400

    transactions = InventoryTransaction.query.filter(
        InventoryTransaction.date_taken >= start_date,
        InventoryTransaction.date_taken <= end_date,
    ).all()

    report = [
        {
            "inventory_id": transaction.inventory_id,
            "product_name": transaction.inventory.product_name,
            "quantity_taken": transaction.quantity_taken,
            "date_taken": transaction.date_taken.isoformat(),
        }
        for transaction in transactions
    ]

    if request.args.get("download") == "true":
        # Create a DataFrame
        df = pd.DataFrame(report)

        # Save to a BytesIO object
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventory Taken")
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="inventory_taken_report.xlsx",
        )

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
