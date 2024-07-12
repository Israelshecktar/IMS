from flask import Flask, request, url_for, session, send_file, redirect, render_template, flash, jsonify
import io
import pandas as pd
from functools import wraps
from models import db, Inventory, User, InventoryTransaction
from itsdangerous import URLSafeTimedSerializer
from config import (
    SQLALCHEMY_DATABASE_URI,
    SECRET_KEY,
    MAIL_SERVER,
    MAIL_PORT,
    MAIL_USE_TLS,
    MAIL_USERNAME,
    MAIL_PASSWORD,
    MAIL_DEFAULT_SENDER,
)
from flask_mail import Mail, Message
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta

app = Flask(__name__)

app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USE_TLS"] = MAIL_USE_TLS
app.config["MAIL_USERNAME"] = MAIL_USERNAME
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD
app.config["MAIL_DEFAULT_SENDER"] = MAIL_DEFAULT_SENDER
app.config["SECRET_KEY"] = SECRET_KEY

mail = Mail(app)
db.init_app(app)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# user Authentication management
@app.route("/login", methods=["GET", "POST"])
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["username"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("index.html", error="Invalid credentials")
    return render_template("index.html")


@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        role = request.form.get("role")

        if not password:
            return render_template("register.html", error="Password cannot be empty")

        if role not in ["admin", "management", "staff"]:
            return render_template("register.html", error="Invalid role selected")

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            return render_template("register.html", error="Username already exists")

        new_user = User(username=username, email=email, role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        # Send email notification
        msg = Message("Welcome to StockGuard", recipients=[new_user.email])
        msg.body = f"Hello {new_user.username},\n\nThank you for registering at StockGuard. Your account has been successfully created."
        mail.send(msg)

        return redirect(url_for("login"))

    return render_template("register.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/request_password_reset", methods=["POST"])
def request_password_reset():
    email = request.form.get("email")
    user = User.query.filter_by(email=email).first()

    if not user:
        return render_template("password_reset.html", error="User not found")

    token = serializer.dumps(user.email, salt="password-reset-salt")
    reset_url = url_for("reset_password", token=token, _external=True)

    msg = Message("Password Reset Request", recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nPlease click the link to reset your password: {reset_url}"
    mail.send(msg)

    return render_template(
        "password_reset_sent.html", message="Password reset link sent to your email"
    )


@app.route("/reset_password/<token>", methods=["POST"])
def reset_password(token):
    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except:
        return render_template(
            "reset_password.html", error="The reset link is invalid or has expired."
        )

    user = User.query.filter_by(email=email).first_or_404()
    password = request.form.get("password")
    user.set_password(password)

    db.session.commit()

    msg = Message("Password Reset Successful", recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nYour password has been reset successfully."
    mail.send(msg)

    return render_template(
        "reset_password_success.html", message="Password reset successfully"
    )


@app.route("/update_profile", methods=["GET", "POST"])
@login_required
def update_profile():
    user = User.query.filter_by(username=session["username"]).first()
    if request.method == "POST":
        user.username = request.form.get("username")
        user.email = request.form.get("email")
        password = request.form.get("password")
        if password:
            user.set_password(password)
        db.session.commit()
        # Send confirmation email
        msg = Message("Profile Update Successful", recipients=[user.email])
        msg.body = (
            f"Hello {user.username},\n\nYour profile has been updated successfully."
        )
        mail.send(msg)

        return redirect(url_for("dashboard"))
    return render_template("update_profile.html", user=user)


# inventory management routes
# Home Route
from decimal import Decimal

@app.route("/add_inventory", methods=["GET", "POST"])
def add_inventory():
    if request.method == "POST":
        material = request.form["material"]
        product_name = request.form["product_name"]
        total_litres = Decimal(request.form["total_litres"])
        date_received = request.form["date_received"]
        best_before_date = request.form["best_before_date"]
        location = request.form["location"]

        existing_inventory = Inventory.query.filter_by(material=material).first()
        if existing_inventory:
            existing_inventory.total_litres += total_litres
            existing_inventory.date_received = date_received
            existing_inventory.best_before_date = best_before_date
            existing_inventory.location = location
        else:
            new_inventory = Inventory(
                material=material,
                product_name=product_name,
                total_litres=total_litres,
                date_received=date_received,
                best_before_date=best_before_date,
                location=location,
            )
            db.session.add(new_inventory)

        db.session.commit()
        return redirect(url_for("dashboard"))
    return render_template("add_inventory.html")

@app.route("/take_inventory", methods=["GET", "POST"])
def take_inventory():
    if request.method == "POST":
        material_code = request.form["material"]
        quantity_to_take = int(request.form["quantity"])
        inventory_item = Inventory.query.filter_by(material=material_code).first()

        if not inventory_item:
            flash("Inventory item not found", "danger")
            return redirect(url_for("take_inventory"))

        if quantity_to_take <= 0 or inventory_item.total_litres < quantity_to_take:
            flash("Invalid or insufficient quantity", "danger")
            return redirect(url_for("take_inventory"))

        inventory_item.total_litres -= quantity_to_take
        transaction = InventoryTransaction(
            inventory_id=inventory_item.id, quantity_taken=quantity_to_take
        )
        db.session.add(transaction)
        db.session.commit()

        flash(f"Successfully took {quantity_to_take} litres. Remaining: {inventory_item.total_litres} litres", "success")
        return redirect(url_for("take_inventory"))

    return render_template("take_inventory.html")

@app.route("/get_inventory_details", methods=["POST"])
def get_inventory_details():
    material_code = request.form["material"]
    inventory_item = Inventory.query.filter_by(material=material_code).first()

    if not inventory_item:
        return jsonify({"error": "Inventory item not found"}), 404

    return jsonify({
        "product_name": inventory_item.product_name,
        "total_litres": inventory_item.total_litres,
        "date_received": inventory_item.date_received.strftime("%Y-%m-%d"),
        "best_before_date": inventory_item.best_before_date.strftime("%Y-%m-%d"),
        "location": inventory_item.location
    })

@app.route("/inventory", methods=["GET"])
def get_inventory():
    query = Inventory.query
    material = request.args.get("material")
    product_name = request.args.get("product_name")
    location = request.args.get("location")

    if material:
        query = query.filter(Inventory.material.ilike(f"%{material}%"))
    if product_name:
        query = query.filter(Inventory.product_name.ilike(f"%{product_name}%"))
    if location:
        query = query.filter(Inventory.location.ilike(f"%{location}%"))

    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    inventory_items = pagination.items

    return render_template(
        "inventory_list.html", items=inventory_items, pagination=pagination
    )


@app.route("/update_inventory/<int:id>", methods=["PUT"])
def update_inventory(id):
    inventory_item = Inventory.query.get(id)
    if not inventory_item:
        return render_template("error.html", message="Inventory item not found")

    inventory_item.material = request.form.get("material", inventory_item.material)
    inventory_item.product_name = request.form.get(
        "product_name", inventory_item.product_name
    )
    inventory_item.total_litres = request.form.get(
        "total_litres", inventory_item.total_litres
    )
    inventory_item.date_received = request.form.get(
        "date_received", inventory_item.date_received
    )
    inventory_item.best_before_date = request.form.get(
        "best_before_date", inventory_item.best_before_date
    )
    inventory_item.location = request.form.get("location", inventory_item.location)

    db.session.commit()
    return render_template(
        "update_inventory_success.html", message="Inventory item updated successfully"
    )

@app.route("/delete_inventory", methods=["GET", "POST"])
def delete_inventory():
    if request.method == "POST":
        item_id = request.form["item_id"]
        inventory_item = Inventory.query.get(item_id)
        if not inventory_item:
            flash("Inventory item not found", "danger")
            return redirect(url_for("delete_inventory"))

        db.session.delete(inventory_item)
        db.session.commit()
        flash("Inventory item deleted successfully", "success")
        return redirect(url_for("delete_inventory"))

    inventory_items = Inventory.query.all()
    return render_template("delete_inventory.html", items=inventory_items)


@app.route("/inventory/below_threshold", methods=["GET"])
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
            "total_litres": float(item.total_litres),
            "date_received": item.date_received.isoformat(),
            "best_before_date": item.best_before_date.isoformat(),
            "location": item.location,
        }
        for item in low_inventory_items
    ]

    if request.args.get("download") == "true":
        df = pd.DataFrame(inventory_list)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Low Inventory")
        output.seek(0)
        return send_file(
            output, as_attachment=True, download_name="low_inventory_report.xlsx"
        )

    return jsonify(inventory_list)

@app.route("/inventory/expiring_soon", methods=["GET"])
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
            "total_litres": float(item.total_litres),
            "date_received": item.date_received.isoformat(),
            "best_before_date": item.best_before_date.isoformat(),
            "location": item.location,
        }
        for item in expiring_items
    ]

    if request.args.get("download") == "true":
        df = pd.DataFrame(inventory_list)
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
        df = pd.DataFrame(report)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventory Levels")
        output.seek(0)
        return send_file(
            output, as_attachment=True, download_name="inventory_levels_report.xlsx"
        )

    return render_template("inventory_levels_report.html", report=report)


@app.route("/report/inventory_taken", methods=["GET"])
def inventory_taken_report():
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")

    if not start_date or not end_date:
        return render_template(
            "error.html", message="Please provide both start_date and end_date"
        )

    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        return render_template(
            "error.html", message="Invalid date format. Use YYYY-MM-DD"
        )

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
        df = pd.DataFrame(report)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventory Taken")
        output.seek(0)
        return send_file(
            output,
            as_attachment=True,
            download_name="inventory_taken_report.xlsx",
        )

    return render_template("inventory_taken_report.html", report=report)


@app.route("/report/user_activity", methods=["GET"])
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
    return render_template("user_activity_report.html", report=report)


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
