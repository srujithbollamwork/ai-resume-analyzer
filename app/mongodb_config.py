import os
from dotenv import load_dotenv
from pymongo import MongoClient
import bcrypt

# Load environment variables
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("⚠️ MONGO_URI not found in .env")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client["ai_resume_analyzer"]

# Collections
resumes_collection = db["resumes"]
jobs_collection = db["jobs"]
users_collection = db["users"]   # ✅ Users collection


# ===============================
# 🔹 USER AUTH HELPERS
# ===============================

def hash_password(password: str) -> bytes:
    """Hash password securely with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())


def check_password(password: str, hashed: bytes) -> bool:
    """Verify password against stored hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed)


def register_user(email: str, password: str, role: str = "user"):
    """Register a new user with hashed password."""
    if users_collection.find_one({"email": email}):
        return {"error": "User already exists"}

    hashed_pw = hash_password(password)
    users_collection.insert_one({
        "email": email,
        "password": hashed_pw,
        "role": role
    })
    return {"success": True}


def authenticate_user(email: str, password: str):
    """Authenticate user by email + password."""
    user = users_collection.find_one({"email": email})
    if not user:
        return None

    if not check_password(password, user["password"]):
        return None

    # ✅ Ensure consistent return type: MongoDB user doc (as dict)
    return {
        "email": user["email"],
        "role": user.get("role", "user")
    }
