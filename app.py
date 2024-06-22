#!/usr/bin/env python3

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Configuration
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database connection
db = SQLAlchemy(app)
migrate = Migrate(app, db)


@app.route("/")
def index():
    return "Hello Shecktar!"


if __name__ == "__main__":
    app.run(debug=True)
