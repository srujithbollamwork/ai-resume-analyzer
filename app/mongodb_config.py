import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("⚠️ MONGO_URI not set in .env")

client = MongoClient(MONGO_URI)
db = client["ai_resume_analyzer"]   # database name
resumes_collection = db["resumes"]  # collection name
