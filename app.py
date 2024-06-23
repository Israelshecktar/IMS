from flask import Flask, request, jsonify
from models import db, RawMaterials
from config import SQLALCHEMY_DATABASE_URI

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

# Home Route
@app.route('/')
def home():
    return ('Hello Shecktar!, your app is running and connected to the inventory db')


# Route to add a raw material
@app.route("/add_raw_material", methods=["POST"])
def add_raw_material():
    # Extract data from the request
    data = request.get_json()

    # Create a new RawMaterials instance
    new_material = RawMaterials(
        category_id=data["category_id"],
        name=data["name"],
        quantity=data["quantity"],
        unit=data["unit"],
        price_per_unit=data["price_per_unit"],
        supplier=data["supplier"],
        received_date=data["received_date"],
    )

    # Add the new material to the session and commit to the database
    db.session.add(new_material)
    db.session.commit()

    return jsonify({"message": "Raw material added successfully"}), 201


@app.route("/raw_materials", methods=["GET"])
def get_raw_materials():
    # Query the database for all raw materials
    raw_materials = RawMaterials.query.all()

    # Convert the raw materials to a list of dictionaries to jsonify
    raw_materials_list = [
        {
            "id": material.id,
            "category_id": material.category_id,
            "name": material.name,
            "quantity": material.quantity,
            "unit": material.unit,
            "price_per_unit": material.price_per_unit,
            "supplier": material.supplier,
            "received_date": material.received_date.isoformat(),
            "expiry_date": (
                material.expiry_date.isoformat() if material.expiry_date else None
            ),
        }
        for material in raw_materials
    ]

    # Return the list as a JSON response
    return jsonify(raw_materials_list)


# Run the Flask app
if __name__ == "__main__":
    app.run(debug=True)
