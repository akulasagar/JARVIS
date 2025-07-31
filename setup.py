# setup.py
import os
from webapp import app, db

print("--- Database Setup Script ---")

# Define the path for the database file in the current directory
db_file_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'database.db')
print(f"Database will be created at: {db_file_path}")

# Check if the database already exists
if os.path.exists(db_file_path):
    print("Database file already exists. Deleting it to create a fresh one.")
    os.remove(db_file_path)

# Push an application context to bind the SQLAlchemy object to the app
app.app_context().push()

# Create all the tables defined in your models
print("Creating all database tables...")
db.create_all()

print("--- SUCCESS: Database 'database.db' has been created successfully. ---")
print("You can now run the PyInstaller command.")