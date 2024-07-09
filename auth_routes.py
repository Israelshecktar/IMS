from flask import Blueprint, request, jsonify, url_for
from models import db, User
from itsdangerous import URLSafeTimedSerializer
from config import JWT_SECRET_KEY, MAIL_USERNAME
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from flask_mail import Mail, Message

auth_bp = Blueprint("auth", __name__)

# Initialize serializer and mail
serializer = URLSafeTimedSerializer(JWT_SECRET_KEY)
mail = Mail()


@auth_bp.route("/register", methods=["POST"])
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


@auth_bp.route("/request_password_reset", methods=["POST"])
def request_password_reset():
    data = request.get_json()
    user = User.query.filter_by(email=data["email"]).first()

    if not user:
        return jsonify({"message": "User not found"}), 404

    token = serializer.dumps(user.email, salt="password-reset-salt")
    reset_url = url_for("auth.reset_password", token=token, _external=True)

    msg = Message("Password Reset Request", recipients=[user.email])
    msg.body = f"Hello {user.username},\n\nPlease click the link to reset your password: {reset_url}"
    mail.send(msg)

    return jsonify({"message": "Password reset link sent to your email"}), 200


@auth_bp.route("/reset_password/<token>", methods=["POST"])
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


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data["username"]).first()
    if user and user.check_password(data["password"]):
        access_token = create_access_token(
            identity={"username": user.username, "role": user.role}
        )
        return jsonify(access_token=access_token), 200
    return jsonify({"message": "Invalid credentials"}), 401


@auth_bp.route("/update_profile", methods=["PUT"])
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
