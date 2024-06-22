#!/usr/bin/env python3


from flask import Flask
from sqlalchemy import create_engine, MetaData
from models import db

# Assuming your Flask app is defined in a file named 'app.py'
# If it's defined in another file, replace 'app' with the correct module name
from app import app

engine = create_engine(app.config["SQLALCHEMY_DATABASE_URI"])
metadata = MetaData()

metadata.reflect(bind=engine)

for table_name, table in metadata.tables.items():
    print(f"Table {table_name}:")
    for column in table.c:
        print(f" - {column.name}: {column.type}")
