# test_db.py
import os
from dotenv import load_dotenv
load_dotenv()

# Check what URL is actually being used
print("DB URL:", os.getenv("DATABASE_URL"))

from app import create_app
from app.extensions import db

app = create_app()

with app.app_context():
    print("SQLAlchemy URL:", app.config["SQLALCHEMY_DATABASE_URI"])
    db.create_all()
    print("✅ Done!")