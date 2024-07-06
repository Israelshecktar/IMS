from flask import Flask, request, jsonify
from models import db, Inventory
from config import SQLALCHEMY_DATABASE_URI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Home Route
@app.route('/')
def home():
    return 'Hello Shecktar!, your app is running and connected to the stockguard db'

# Route to add an inventory item
@app.route("/add_inventory", methods=["POST"])
def add_inventory():
    data = request.get_json()
    new_inventory = Inventory(
        material=data["material"],
        product_name=data["product_name"],
        total_litres=data["total_litres"],
        date_received=data["date_received"],
        best_before_date=data["best_before_date"],
        location=data["location"]
    )
    db.session.add(new_inventory)
    db.session.commit()
    return jsonify({"message": "Inventory item added successfully"}), 201

# Route to get all inventory items
@app.route("/inventory", methods=["GET"])
def get_inventory():
    inventory_items = Inventory.query.all()
    inventory_list = [
        {
            "id": item.id,
            "material": item.material,
            "product_name": item.product_name,
            "total_litres": item.total_litres,
            "date_received": item.date_received.isoformat(),
            "best_before_date": item.best_before_date.isoformat(),
            "location": item.location
        }
        for item in inventory_items
    ]
    return jsonify(inventory_list)

# Route to get the names of HEMPEL products in stock
@app.route("/hempel_products", methods=["GET"])
def get_hempel_products():
    hempel_products = Inventory.query.with_entities(Inventory.product_name).all()
    product_names = [product.product_name for product in hempel_products]
    return jsonify(product_names)

# Initialize the database
with app.app_context():
    db.create_all()

# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
