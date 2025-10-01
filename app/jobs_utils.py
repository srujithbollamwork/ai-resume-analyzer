import os
import re
import requests
import pandas as pd
from dotenv import load_dotenv
from pymongo import UpdateOne
from app.mongodb_config import jobs_collection

# Load env vars
load_dotenv()
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")


# ---------------------------
# Helpers
# ---------------------------
def clean_col_names(df):
    """Normalize CSV column names."""
    new_cols = []
    for col in df.columns:
        new_col = re.sub(r'[^A-Za-z0-9_]+', '', col.lower().strip().replace(' ', '_'))
        new_cols.append(new_col)
    df.columns = new_cols
    return df


# ---------------------------
# Jooble API
# ---------------------------
def fetch_from_jooble(keywords="Python Developer", location="India", page=1, limit=20):
    """Fetch jobs from Jooble API."""
    if not JOOBLE_API_KEY:
        print("⚠️ JOOBLE_API_KEY not found. Skipping API fetch.")
        return []

    url = f"https://jooble.org/api/{JOOBLE_API_KEY}"
    payload = {"keywords": keywords, "location": location, "page": page}

    try:
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()
        return data.get("jobs", [])[:limit]
    except Exception as e:
        print(f"⚠️ Jooble API error: {e}")
        return []


# ---------------------------
# CSV Import
# ---------------------------
def import_jobs_from_csv(csv_path="jobs_sample.csv"):
    """Import jobs from CSV into MongoDB."""
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        return {"error": f"⚠️ Failed to read CSV: {e}"}

    if len(df.columns) == 1 and "," in df.columns[0]:
        print("⚠️ Malformed header detected. Fixing...")
        df = df[df.columns[0]].str.split(",", expand=True)
        header_df = pd.read_csv(csv_path, nrows=0)
        df.columns = [col.strip() for col in header_df.columns[0].split(",")]

    df = clean_col_names(df)
    print(f"Cleaned CSV columns: {list(df.columns)}")

    if not {"title", "company"}.issubset(df.columns):
        return {"error": "⚠️ CSV must contain 'title' and 'company' columns."}

    initial_count = len(df)
    df.dropna(subset=["title", "company"], inplace=True)
    print(f"Filtered out {initial_count - len(df)} rows with missing title/company.")

    records = df.to_dict(orient="records")
    return save_jobs_to_mongo(records)


# ---------------------------
# MongoDB Upsert
# ---------------------------
def save_jobs_to_mongo(job_list):
    """Upsert jobs into MongoDB."""
    if not job_list:
        return {"inserted": 0, "updated": 0, "message": "⚠️ No jobs to save."}

    # Ensure unique index exists
    jobs_collection.create_index([("title", 1), ("company", 1)], unique=True, sparse=True)

    ops = []
    for job in job_list:
        doc = {
            "title": job.get("title"),
            "company": job.get("company"),
            "location": job.get("location"),
            "description": job.get("description") or job.get("snippet"),
            "skills_required": job.get("skills_required", ""),
            "link": job.get("link"),
            "updated": job.get("updated"),
        }
        if doc["title"] and doc["company"]:
            ops.append(
                UpdateOne(
                    {"title": doc["title"], "company": doc["company"]},
                    {"$set": doc},
                    upsert=True,
                )
            )

    if not ops:
        return {"error": "⚠️ No valid operations created."}

    result = jobs_collection.bulk_write(ops)
    return {
        "inserted": result.upserted_count,
        "updated": result.modified_count,
        "message": "✅ Jobs imported/updated successfully."
    }


# ---------------------------
# Refresh (Jooble → Mongo)
# ---------------------------
def refresh_jobs(keywords="Data Scientist", location="India", limit=10):
    """Fetch jobs (API first, fallback to CSV) and save to MongoDB."""
    jobs_list = fetch_from_jooble(keywords, location, limit=limit)
    if not jobs_list:  # fallback
        jobs_list = import_jobs_from_csv("jobs_sample.csv")
        if isinstance(jobs_list, dict):  # already formatted result
            return jobs_list
    return save_jobs_to_mongo(jobs_list)


# ---------------------------
# CLI Test
# ---------------------------
if __name__ == "__main__":
    print("🔄 Fetching jobs from Jooble...")
    result = refresh_jobs("Data Scientist", "India", limit=10)
    print(result)

    print("📂 Importing jobs from CSV...")
    result = import_jobs_from_csv("jobs_sample.csv")
    print(result)
