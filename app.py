from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "mysql+pymysql://shecktar:Shecktar13$@localhost:3306/inventory_db"
    )
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        from models import User, Category, Material

    @app.route("/")
    def index():
        return "Hello Shecktar!"

    @app.route("/test_connection")
    def test_connection():
        try:
            # Try to query the users table
            users = User.query.all()
            return f"Connection successful! Found {len(users)} users."
        except Exception as e:
            return f"Connection failed: {str(e)}"

    @app.shell_context_processor
    def make_shell_context():
        return {"db": db, "User": User, "Category": Category, "Material": Material}

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
