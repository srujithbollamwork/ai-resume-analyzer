from pymongo import MongoClient
import os
from dotenv import load_dotenv

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client["ai_resume_analyzer"]
resumes = db["resumes"]

resumes.insert_one({"test": "hello world"})
print("Inserted test document ✅")
