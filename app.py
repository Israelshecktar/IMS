from flask import Flask
from models import db, User, Category, RawMaterials, PackagingMaterials

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://shecktar:Shecktar13$@localhost/inventory_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize the database with the Flask app
db.init_app(app)

# Create the database tables
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return 'Hello, shecktar! Your Flask app is connected to the database and ready to manage inventory.'

if __name__ == '__main__':
    app.run(debug=True)
