import os
from dotenv import load_dotenv
from pymongo import MongoClient
import bcrypt

# ===============================
# 🔹 Load environment variables
# ===============================
load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise ValueError("⚠️ MONGO_URI not found in .env")

# ===============================
# 🔹 Connect to MongoDB
# ===============================
client = MongoClient(MONGO_URI)
db = client["ai_resume_analyzer"]

# Collections
resumes_collection = db["resumes"]
jobs_collection = db["jobs"]
users_collection = db["users"]

# ===============================
# 🔹 Superadmin Configuration
# ===============================
SUPERADMIN_EMAIL = "srujithbollamwork@gmail.com"
SUPERADMIN_ROLE = "superadmin"
SUPERADMIN_DEFAULT_PASSWORD = "supersecure123"  # ⚠️ Change this in .env later

# Auto-create superadmin if missing
if not users_collection.find_one({"email": SUPERADMIN_EMAIL}):
    hashed_pw = bcrypt.hashpw(SUPERADMIN_DEFAULT_PASSWORD.encode("utf-8"), bcrypt.gensalt())
    users_collection.insert_one({
        "email": SUPERADMIN_EMAIL,
        "password": hashed_pw,
        "role": SUPERADMIN_ROLE
    })
    print(f"✅ Superadmin {SUPERADMIN_EMAIL} created with default password.")

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
    """Register a new user with hashed password.
       Prevents direct admin/superadmin registration."""
    if users_collection.find_one({"email": email}):
        return {"error": "User already exists"}

    # Force role to "user" always (only superadmin can promote)
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
# 🔹 Admin Safety Helpers
# ===============================

def protect_superadmin(user_email: str) -> bool:
    """Check if user is superadmin and block changes."""
    return user_email == SUPERADMIN_EMAIL


def safe_update_role(email: str, new_role: str):
    """Update role but protect superadmin."""
    if protect_superadmin(email):
        return {"error": "❌ Cannot modify superadmin"}
    users_collection.update_one({"email": email}, {"$set": {"role": new_role}})
    return {"success": True, "role": new_role}


def safe_delete_user(email: str):
    """Delete user but protect superadmin."""
    if protect_superadmin(email):
        return {"error": "❌ Cannot delete superadmin"}
    users_collection.delete_one({"email": email})
    return {"success": True}
