from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

app = Flask(__name__)

# Configuration with URL-encoded password
app.config["SQLALCHEMY_DATABASE_URI"] = (
    "mysql+pymysql://shecktar:Abolanle12%40@localhost/inventory_db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database connection
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import models
from models import User, Category, Material


@app.route("/")
def index():
    return "Hello Shecktar!"


@app.route("/test_db")
def test_db():
    # Add a new category
    new_category = Category(category_name="Test Category")
    db.session.add(new_category)
    db.session.commit()

    # Query all categories
    categories = Category.query.all()
    return ", ".join([category.category_name for category in categories])


@app.shell_context_processor
def make_shell_context():
    return {"db": db, "User": User, "Category": Category, "Material": Material}


if __name__ == "__main__":
    app.run(debug=True)
