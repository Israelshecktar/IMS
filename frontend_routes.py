from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.route("/")
def landing_page():
    return render_template("index.html")


@frontend_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")
