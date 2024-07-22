from app import app, db
from models import Category

# List of categories to add
categories = [
    {"name": "Pigments", "description": "Colorants used in paint formulations"},
    {
        "name": "Additives",
        "description": "Substances added to improve paint properties",
    },
    {
        "name": "Resins",
        "description": "Binders that hold the pigment particles together",
    },
    {
        "name": "Solvents",
        "description": "Liquids used to dissolve or disperse other components",
    },
    {
        "name": "Extenders",
        "description": "Fillers that extend the volume of the paint without affecting its properties",
    },
]

# Wrap the operations in an application context
with app.app_context():
    # Add each category to the database
    for category_info in categories:
        category = Category(**category_info)
        db.session.add(category)
    # Commit the changes to the database
    db.session.commit()
