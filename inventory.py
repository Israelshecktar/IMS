import pandas as pd
from datetime import date
from models import db, Inventory
from app import app

# Read the CSV file, specifying the correct header row
df = pd.read_csv("hempel.csv", header=0)

# Define the current date and best before date
current_date = date.today()
best_before_date = date(2024, 12, 31)


# Function to insert data into the database
def insert_data():
    with app.app_context():
        for index, row in df.iterrows():
            inventory_item = Inventory(
                material=row["Material"],
                product_name=row["Material description"],
                total_litres=row["Physical"],
                date_received=current_date,
                best_before_date=best_before_date,
                location="RMr1",
            )
            db.session.add(inventory_item)
        db.session.commit()


# Call the function to insert data
insert_data()
