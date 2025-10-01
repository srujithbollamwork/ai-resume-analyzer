import os
from dotenv import load_dotenv
from pymongo import MongoClient
import bcrypt

# ===============================
# 🔹 Load Environment
# ===============================
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("⚠️ MONGO_URI not found in .env")

# ===============================
# 🔹 MongoDB Setup
# ===============================
client = MongoClient(MONGO_URI)
db = client["ai_resume_analyzer"]

# Collections
resumes_collection = db["resumes"]
jobs_collection = db["jobs"]
users_collection = db["users"]

# Superadmin email (hardcoded for protection)
SUPERADMIN_EMAIL = "srujithbollamwork@gmail.com"

# ===============================
# 🔹 Password Helpers
# ===============================
def hash_password(password: str) -> bytes:
    """Hash password securely with bcrypt."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())

def check_password(password: str, hashed: bytes) -> bool:
    """Verify password against stored hash."""
    return bcrypt.checkpw(password.encode("utf-8"), hashed)

# ===============================
# 🔹 User Management
# ===============================
def register_user(email: str, password: str, role: str = "user"):
    """Register a new user (only users, never admins)."""
    if users_collection.find_one({"email": email}):
        return {"error": "User already exists"}

    # 🚫 Prevent new admins from registering directly
    if role != "user":
        role = "user"

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

    return {
        "email": user["email"],
        "role": user.get("role", "user")
    }

# ===============================
# 🔹 Safe Admin Controls
# ===============================
def safe_update_role(email: str, current_role: str):
    """Toggle role between admin and user (never touch superadmin)."""
    if email == SUPERADMIN_EMAIL:
        return {"error": "Superadmin role cannot be changed"}

    new_role = "admin" if current_role == "user" else "user"
    users_collection.update_one({"email": email}, {"$set": {"role": new_role}})
    return {"success": True, "new_role": new_role}

def safe_delete_user(email: str):
    """Delete a user safely (superadmin cannot be deleted)."""
    if email == SUPERADMIN_EMAIL:
        return {"error": "Superadmin cannot be deleted"}

    users_collection.delete_one({"email": email})
    return {"success": True}
