from app import app, db
import os

with app.app_context():
    # Drop all tables to ensure a clean slate (fixes schema mismatches)
    db.drop_all()
    db.create_all()
    print("Database initialized successfully! (Old tables dropped and recreated)")
