import bcrypt
from app.mongodb_config import users_collection


def signup_user(email, password):
    if users_collection.find_one({"email": email}):
        return {"success": False, "message": "⚠️ User already exists"}

    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    users_collection.insert_one({
        "email": email,
        "password": hashed,
        "role": "user"  # ✅ default role
    })
    return {"success": True, "message": "✅ User created successfully"}


def login_user(email, password):
    user = users_collection.find_one({"email": email})
    if not user:
        return {"success": False, "message": "⚠️ User not found"}

    if bcrypt.checkpw(password.encode("utf-8"), user["password"]):
        return {"success": True, "message": "✅ Login successful", "role": user.get("role", "user")}
    else:
        return {"success": False, "message": "⚠️ Incorrect password"}
