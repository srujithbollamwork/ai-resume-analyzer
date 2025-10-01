from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("⚠️ MONGO_URI not found in .env")

# Connect once and reuse
client = MongoClient(MONGO_URI)
db = client["ai_resume_analyzer"]
jobs = db["jobs"]


def get_jobs(limit=20, search_query=None):
    """
    Fetch jobs from MongoDB.
    - limit: max number of jobs to return
    - search_query: optional dict for filtering (MongoDB query)
    """
    query = search_query if search_query else {}
    results = list(jobs.find(query).limit(limit))

    # Convert ObjectId to string for JSON/Streamlit compatibility
    for job in results:
        job["_id"] = str(job["_id"])

    return results
