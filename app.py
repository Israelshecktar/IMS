# Import necessary libraries and modules
from flask import (
    Flask,
    request,
    url_for,
    session,
    send_file,
    redirect,
    render_template,
    flash,
    jsonify,
)
import io
import pandas as pd
from functools import wraps
from decimal import Decimal
from models import db, Inventory, User, InventoryTransaction, DeletedInventory
from itsdangerous import URLSafeTimedSerializer
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from pytz import timezone
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
from datetime import datetime, timedelta

# Initialize Flask app
app = Flask(__name__)

# Configure app with database and mail settings from config.py
app.config["SQLALCHEMY_DATABASE_URI"] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["MAIL_SERVER"] = MAIL_SERVER
app.config["MAIL_PORT"] = MAIL_PORT
app.config["MAIL_USE_TLS"] = MAIL_USE_TLS
app.config["MAIL_USERNAME"] = MAIL_USERNAME
app.config["MAIL_PASSWORD"] = MAIL_PASSWORD
app.config["MAIL_DEFAULT_SENDER"] = MAIL_DEFAULT_SENDER
app.config["SECRET_KEY"] = SECRET_KEY

# Initialize Flask-Mail and SQLAlchemy
mail = Mail(app)
db.init_app(app)


# Decorator function to enforce login required for certain routes
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "username" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)

    return decorated_function


# Route for user login
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



# Route for dashboard, accessible only after login
@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")


# Route for user registration
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

        # Send email notification to the new user
        msg = Message("Welcome to StockGuard", recipients=[new_user.email])
        msg.body = f"Hello {new_user.username},\n\nThank you for registering at StockGuard. Your account has been successfully created."
        mail.send(msg)

        return redirect(url_for("login"))

    return render_template("register.html")


# Route for user logout
@app.route("/logout")
def logout():
    # Clear the session to log the user out
    session.clear()
    return redirect(url_for("login"))


# Route to request password reset
@app.route("/request_password_reset", methods=["POST"])
def request_password_reset():
    # Get the email from the form
    email = request.form.get("email")
    # Find the user by email
    user = User.query.filter_by(email=email).first()

    # If user is not found, return an error
    if not user:
        return render_template("password_reset.html", error="User not found")

    # Generate a password reset token
    token = serializer.dumps(user.email, salt="password-reset-salt")
    # Create a password reset URL
    reset_url = url_for("reset_password", token=token, _external=True)

    # Send a password reset email to the user
    msg = Message("Password Reset Request", recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nPlease click the link to reset your password: {reset_url}"
    mail.send(msg)

    # Inform the user that a password reset link has been sent
    return render_template(
        "password_reset_sent.html", message="Password reset link sent to your email"
    )


# Route to reset password
@app.route("/reset_password/<token>", methods=["POST"])
def reset_password(token):
    try:
        # Verify the token and get the email
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)
    except:
        # If token is invalid or expired, return an error
        return render_template(
            "reset_password.html", error="The reset link is invalid or has expired."
        )

    # Find the user by email
    user = User.query.filter_by(email=email).first_or_404()
    # Get the new password from the form
    password = request.form.get("password")
    # Set the new password for the user
    user.set_password(password)

    # Commit the changes to the database
    db.session.commit()

    # Send a confirmation email to the user
    msg = Message("Password Reset Successful", recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nYour password has been reset successfully."
    mail.send(msg)

    # Inform the user that the password has been reset
    return render_template(
        "reset_password_success.html", message="Password reset successfully"
    )


# Route to update user profile
@app.route("/update_profile", methods=["GET", "POST"])
@login_required
def update_profile():
    # Get the current user's information
    user = User.query.filter_by(username=session["username"]).first()
    if request.method == "POST":
        # Update user information from the form
        user.username = request.form.get("username")
        user.email = request.form.get("email")
        password = request.form.get("password")
        if password:
            # Set the new password if provided
            user.set_password(password)
        # Commit the changes to the database
        db.session.commit()
        # Send a confirmation email to the user
        msg = Message("Profile Update Successful", recipients=[user.email])
        msg.body = (
            f"Hello {user.username},\n\nYour profile has been updated successfully."
        )
        mail.send(msg)

        # Redirect to the dashboard
        return redirect(url_for("dashboard"))
    # Render the profile update template
    return render_template("update_profile.html", user=user)


# Routes for Inventory Management
# Route to view full inventory
@app.route("/view_full_inventory", methods=["GET"])
@login_required
def view_full_inventory():
    # Query all inventory items
    inventory_items = Inventory.query.all()
    # Render the HTML template and pass the inventory items to it
    return render_template("full_inventory.html", inventory_items=inventory_items)


# Route to add inventory
@app.route("/add_inventory", methods=["GET", "POST"])
@login_required
def add_inventory():
    if request.method == "POST":
        try:
            # Get inventory details from the form
            material = request.form[
                "material"
            ].strip()  # Remove any leading/trailing whitespace
            product_name = request.form["product_name"]
            total_litres = Decimal(request.form["total_litres"])
            date_received = request.form["date_received"]
            best_before_date = request.form["best_before_date"]
            location = request.form["location"]

            # Validate input values
            if not material or not product_name or total_litres <= 0:
                flash("Invalid input values. Please check your entries.", "error")
                return redirect(url_for("add_inventory"))

            # Check if the inventory item already exists
            existing_inventory = Inventory.query.filter_by(material=material).first()
            if existing_inventory:
                # Update existing inventory
                existing_inventory.total_litres += total_litres
                existing_inventory.date_received = date_received
                existing_inventory.best_before_date = best_before_date
                existing_inventory.location = location
            else:
                # Add new inventory item
                new_inventory = Inventory(
                    material=material,
                    product_name=product_name,
                    total_litres=total_litres,
                    date_received=date_received,
                    best_before_date=best_before_date,
                    location=location,
                )
                db.session.add(new_inventory)

            # Commit the changes to the database
            db.session.commit()
            flash("Inventory added successfully!", "success")
            return redirect(url_for("dashboard"))
        except Exception as e:
            # Rollback the transaction in case of error
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "error")
            return redirect(url_for("add_inventory"))
    # Render the add inventory template
    return render_template("add_inventory.html")


# Route to take inventory
@app.route("/take_inventory", methods=["GET", "POST"])
@login_required
def take_inventory():
    if request.method == "POST":
        # Get material code and quantity to take from the form
        material_code = request.form["material"]
        quantity_to_take = int(request.form["quantity"])
        inventory_item = Inventory.query.filter_by(material=material_code).first()

        # Check if inventory item exists
        if not inventory_item:
            flash("Inventory item not found", "danger")
            return redirect(url_for("take_inventory"))

        # Validate quantity to take
        if quantity_to_take <= 0 or inventory_item.total_litres < quantity_to_take:
            flash("Invalid or insufficient quantity", "danger")
            return redirect(url_for("take_inventory"))

        # Update inventory and create a transaction record
        inventory_item.total_litres -= quantity_to_take
        transaction = InventoryTransaction(
            inventory_id=inventory_item.id, quantity_taken=quantity_to_take
        )
        db.session.add(transaction)
        db.session.commit()

        flash(
            f"Successfully took {quantity_to_take} litres. Remaining: {inventory_item.total_litres} litres",
            "success",
        )
        return redirect(url_for("take_inventory"))

    # Render the take inventory template
    return render_template("take_inventory.html")


# Route to get inventory details by material code
@app.route("/get_inventory_details", methods=["POST"])
@login_required
def get_inventory_details():
    # Get material code from the form
    material_code = request.form["material"]
    inventory_item = Inventory.query.filter_by(material=material_code).first()

    # Check if inventory item exists
    if not inventory_item:
        return jsonify({"error": "Inventory item not found"}), 404

    # Return inventory details as JSON
    return jsonify(
        {
            "product_name": inventory_item.product_name,
            "total_litres": inventory_item.total_litres,
            "date_received": inventory_item.date_received.strftime("%Y-%m-%d"),
            "best_before_date": inventory_item.best_before_date.strftime("%Y-%m-%d"),
            "location": inventory_item.location,
        }
    )


# Route to get total inventory count
@app.route("/inventory/total", methods=["GET"])
@login_required
def get_total_inventory():
    total_products = Inventory.query.count()
    return jsonify(total=total_products)


# Route to get inventory with filtering and pagination
@app.route("/inventory", methods=["GET"])
@login_required
def get_inventory():
    query = Inventory.query
    material = request.args.get("material")
    product_name = request.args.get("product_name")
    location = request.args.get("location")

    # Apply filters if provided
    if material:
        query = query.filter(Inventory.material.ilike(f"%{material}%"))
    if product_name:
        query = query.filter(Inventory.product_name.ilike(f"%{product_name}%"))
    if location:
        query = query.filter(Inventory.location.ilike(f"%{location}%"))

    # Pagination settings
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    inventory_items = pagination.items

    # Render the inventory list template with pagination
    return render_template(
        "inventory_list.html", items=inventory_items, pagination=pagination
    )


# Route to get inventory details by material code (JSON)
@app.route("/get_inventory_by_material", methods=["POST"])
@login_required
def get_inventory_by_material():
    try:
        # Get material code from the JSON request
        material_code = request.json["material"]
        inventory_item = Inventory.query.filter_by(material=material_code).first()

        # Check if inventory item exists
        if not inventory_item:
            return jsonify({"error": "Inventory item not found"}), 404

        # Return inventory details as JSON
        return jsonify(
            {
                "id": inventory_item.id,
                "material": inventory_item.material,
                "product_name": inventory_item.product_name,
                "total_litres": str(inventory_item.total_litres),
                "date_received": inventory_item.date_received.strftime("%Y-%m-%d"),
                "best_before_date": inventory_item.best_before_date.strftime(
                    "%Y-%m-%d"
                ),
                "location": inventory_item.location,
            }
        )
    except Exception as e:
        # Handle any exceptions and return an error message
        return jsonify({"error": str(e)}), 500


# Route to update inventory
@app.route("/update_inventory", methods=["GET", "POST"])
@login_required
def update_inventory():
    if request.method == "POST":
        try:
            # Get inventory item ID from the form
            inventory_item_id = request.form["id"]
            inventory_item = Inventory.query.get(inventory_item_id)
            if not inventory_item:
                flash("Inventory item not found", "error")
                return redirect(url_for("update_inventory"))

            # Confirmation check before updating
            confirm = request.form.get("confirm_update")
            if confirm != "yes":
                flash("Update cancelled by user.", "info")
                return redirect(url_for("update_inventory", id=inventory_item_id))

            # Update inventory item details
            inventory_item.material = request.form["material"]
            inventory_item.product_name = request.form["product_name"]
            inventory_item.total_litres = Decimal(request.form["total_litres"])
            inventory_item.date_received = request.form["date_received"]
            inventory_item.best_before_date = request.form["best_before_date"]
            inventory_item.location = request.form["location"]

            # Commit the changes to the database
            db.session.commit()
            flash("Inventory item updated successfully!", "success")
        except Exception as e:
            # Rollback the transaction in case of error
            db.session.rollback()
            flash(f"An error occurred: {str(e)}", "error")
        finally:
            return redirect(url_for("dashboard"))
    else:
        # Get inventory item ID from the query parameters
        inventory_item_id = request.args.get("id")
        inventory_item = (
            Inventory.query.get(inventory_item_id) if inventory_item_id else None
        )
        # Render the update inventory template
        return render_template("update_inventory.html", inventory_item=inventory_item)


# Route to delete inventory item
@app.route("/delete_inventory", methods=["GET", "POST"])
@login_required
def delete_inventory():
    if request.method == "POST":
        # Get the ID of the item to be deleted
        item_id = request.form["item_id"]
        inventory_item = Inventory.query.get(item_id)
        # Check if the inventory item exists
        if not inventory_item:
            flash("Inventory item not found", "danger")
            return redirect(url_for("delete_inventory"))

        # Check for related transactions before deleting
        related_transactions = InventoryTransaction.query.filter_by(
            inventory_id=inventory_item.id
        ).all()
        if related_transactions:
            flash("Cannot delete inventory item with related transactions", "danger")
            return redirect(url_for("delete_inventory"))

        # Store deleted inventory details for record-keeping
        deleted_inventory = DeletedInventory(
            original_id=inventory_item.id,
            material=inventory_item.material,
            product_name=inventory_item.product_name,
            total_litres=inventory_item.total_litres,
            date_received=inventory_item.date_received,
            best_before_date=inventory_item.best_before_date,
            location=inventory_item.location,
        )
        db.session.add(deleted_inventory)

        # Delete the inventory item from the database
        db.session.delete(inventory_item)
        db.session.commit()
        flash("Inventory item deleted successfully and details stored", "success")
        return redirect(url_for("delete_inventory"))

    # Get all inventory items for display
    inventory_items = Inventory.query.all()
    return render_template("delete_inventory.html", items=inventory_items)


# Route to view deleted inventory items
@app.route("/deleted_inventory", methods=["GET"])
@login_required
def view_deleted_inventory():
    # Get all deleted inventory items
    deleted_items = DeletedInventory.query.all()
    return render_template("deleted_inventory.html", items=deleted_items)


# Route to get inventory items below a certain threshold
@app.route("/inventory/below_threshold", methods=["GET"])
def get_inventory_below_threshold():
    # Set the threshold for low inventory
    threshold = 50
    # Query inventory items below the threshold
    low_inventory_items = Inventory.query.filter(
        Inventory.total_litres <= threshold
    ).all()
    # Prepare inventory list for JSON response or download
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

    # Check if the request is for a downloadable report
    if request.args.get("download") == "true":
        # Convert inventory list to a DataFrame and write to an Excel file
        df = pd.DataFrame(inventory_list)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Low Inventory")
        output.seek(0)
        # Send the Excel file as a downloadable response
        return send_file(
            output, as_attachment=True, download_name="low_inventory_report.xlsx"
        )

    # Return inventory list as JSON response
    return jsonify(inventory_list)


# Route to get inventory items expiring soon
@app.route("/inventory/expiring_soon", methods=["GET"])
@login_required
def get_inventory_expiring_soon():
    # Calculate the date three months from now
    three_months_from_now = datetime.now() + timedelta(days=90)
    # Query inventory items expiring before the calculated date
    expiring_items = Inventory.query.filter(
        Inventory.best_before_date <= three_months_from_now
    ).all()
    # Prepare inventory list for JSON response or download
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

    # Check if the request is for a downloadable report
    if request.args.get("download") == "true":
        # Convert inventory list to a DataFrame and write to an Excel file
        df = pd.DataFrame(inventory_list)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Expiring Soon")
        output.seek(0)
        # Send the Excel file as a downloadable response
        return send_file(
            output,
            as_attachment=True,
            download_name="expiring_soon_report.xlsx",
        )

    # Return inventory list as JSON response
    return jsonify(inventory_list)


# Reporting and Analytics Routes
# Route to generate inventory levels report
@app.route("/report/inventory_levels", methods=["GET"])
@login_required
def inventory_levels_report():
    # Query all inventory items
    inventory_items = Inventory.query.all()
    # Prepare report data
    report = [
        {
            "product_name": item.product_name,
            "total_litres": item.total_litres,
            "location": item.location,
        }
        for item in inventory_items
    ]

    # Check if the request is for a downloadable report
    if request.args.get("download") == "true":
        # Convert report data to a DataFrame and write to an Excel file
        df = pd.DataFrame(report)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="Inventory Levels")
        output.seek(0)
        # Send the Excel file as a downloadable response
        return send_file(
            output, as_attachment=True, download_name="inventory_levels_report.xlsx"
        )

    # Render the inventory levels report template
    return render_template("inventory_levels_report.html", report=report)


# Route to generate inventory taken report
@app.route("/report/inventory_taken", methods=["GET", "POST"])
@login_required
def inventory_taken_report():
    if request.method == "POST":
        # Get start and end dates from the form
        start_date = request.form.get("start_date")
        end_date = request.form.get("end_date")

        # Validate date inputs
        if not start_date or not end_date:
            flash("Please provide both start date and end date", "danger")
            return redirect(url_for("inventory_taken_report"))

        try:
            start_date = datetime.strptime(start_date, "%Y-%m-%d")
            end_date = datetime.strptime(end_date, "%Y-%m-%d")
        except ValueError:
            flash("Invalid date format. Use YYYY-MM-DD", "danger")
            return redirect(url_for("inventory_taken_report"))

        # Query transactions within the date range
        transactions = InventoryTransaction.query.filter(
            InventoryTransaction.date_taken >= start_date,
            InventoryTransaction.date_taken <= end_date,
        ).all()

        # Prepare report data
        report = [
            {
                "inventory_id": transaction.inventory_id,
                "product_name": transaction.inventory.product_name,
                "quantity_taken": transaction.quantity_taken,
                "date_taken": transaction.date_taken.isoformat(),
            }
            for transaction in transactions
        ]

        # Check if the request is for a downloadable report
        if request.form.get("download") == "true":
            # Convert report data to a DataFrame and write to an Excel file
            df = pd.DataFrame(report)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Inventory Taken")
            output.seek(0)
            # Send the Excel file as a downloadable response
            return send_file(
                output,
                as_attachment=True,
                download_name="inventory_taken_report.xlsx",
            )

        # Render the inventory taken report template
        return render_template("inventory_taken_report.html", report=report)

    # Render the inventory taken report template
    return render_template("inventory_taken_report.html")


# Route to generate user activity report
@app.route("/report/user_activity", methods=["GET"])
def user_activity_report():
    # Query all users
    users = User.query.all()
    # Prepare report data
    report = [
        {
            "username": user.username,
            "email": user.email,
            "role": user.role,
        }
        for user in users
    ]

    # Check if the request is for a downloadable report
    if request.args.get("download") == "true":
        # Convert report data to a DataFrame and write to an Excel file
        df = pd.DataFrame(report)
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="User Activity")
        output.seek(0)
        # Send the Excel file as a downloadable response
        return send_file(
            output,
            as_attachment=True,
            download_name="user_activity_report.xlsx",
        )

    # Render the user activity report template
    return render_template("user_activity_report.html", report=report)


# Automated Email Notifications


# Function to check inventory levels and send email alerts for low inventory
def check_inventory_levels():
    with app.app_context():
        # Query inventory items with total litres below the threshold
        low_inventory_items = Inventory.query.filter(Inventory.total_litres < 50).all()
        if low_inventory_items:
            # Prepare inventory list for the email attachment
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

            # Convert inventory list to a DataFrame and save to a BytesIO object
            df = pd.DataFrame(inventory_list)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Low Inventory")
            output.seek(0)

            # Create the email message with attachment
            msg = Message("Low Inventory Alert", recipients=[MAIL_USERNAME])
            msg.body = "The following products are below the 50 liters threshold. Please find the attached report for details."
            msg.attach(
                "low_inventory_report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                output.read(),
            )
            # Send the email
            mail.send(msg)


# Function to check for expiring products and send email alerts
def check_expiring_products():
    with app.app_context():
        # Calculate the date three months from now
        three_months_from_now = datetime.now() + timedelta(days=90)
        # Query inventory items expiring before the calculated date
        expiring_items = Inventory.query.filter(
            Inventory.best_before_date <= three_months_from_now
        ).all()
        if expiring_items:
            # Prepare inventory list for the email attachment
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

            # Convert inventory list to a DataFrame and save to a BytesIO object
            df = pd.DataFrame(inventory_list)
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                df.to_excel(writer, index=False, sheet_name="Expiring Soon")
            output.seek(0)

            # Create the email message with attachment
            msg = Message("Expiration Notice", recipients=[MAIL_USERNAME])
            msg.body = "The following products are expiring within the next 3 months. Please find the attached report for details."
            msg.attach(
                "expiring_soon_report.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                output.read(),
            )
            # Send the email
            mail.send(msg)


# Scheduling the Tasks

# Initialize the scheduler
scheduler = BackgroundScheduler()
# Schedule the check_inventory_levels function to run every Friday at 10 AM WAT
scheduler.add_job(
    func=check_inventory_levels,
    trigger=CronTrigger(day_of_week="fri", hour=10, minute=0, timezone="Africa/Lagos"),
)
# Schedule the check_expiring_products function to run every Friday at 10 AM WAT
scheduler.add_job(
    func=check_expiring_products,
    trigger=CronTrigger(day_of_week="fri", hour=10, minute=0, timezone="Africa/Lagos"),
)
# Start the scheduler
scheduler.start()

# Initialize the database
with app.app_context():
    db.create_all()

# Run the Flask app
if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True, port=8000)
