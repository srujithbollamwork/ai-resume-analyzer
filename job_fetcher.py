import os
import requests
import pandas as pd
from dotenv import load_dotenv
from pymongo import UpdateOne
from app.mongodb_config import jobs_collection  # ✅ use central config

# Load environment
load_dotenv()
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")


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


def fetch_from_csv(csv_path="jobs_sample.csv"):
    """Fallback: Load jobs from CSV if Jooble API is unavailable."""
    if not os.path.exists(csv_path):
        print(f"⚠️ CSV file not found: {csv_path}")
        return []

    df = pd.read_csv(csv_path)
    required_cols = {"title", "company", "location", "skills_required", "description"}
    if not required_cols.issubset(df.columns):
        print("⚠️ CSV is missing required columns.")
        return []

    return df.to_dict(orient="records")


def save_jobs_to_mongo(job_list):
    """Upsert jobs into MongoDB."""
    if not job_list:
        return {"inserted": 0, "updated": 0, "message": "⚠️ No jobs to save."}

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
        return {"inserted": 0, "updated": 0, "message": "⚠️ No valid jobs to save."}

    result = jobs_collection.bulk_write(ops)
    return {
        "inserted": result.upserted_count,
        "updated": result.modified_count,
        "message": "✅ Jobs updated successfully."
    }


def refresh_jobs(keywords="Data Scientist", location="India", limit=10):
    """Fetch jobs (API or fallback CSV) and save to MongoDB."""
    jobs_list = fetch_from_jooble(keywords, location, limit=limit)

    if not jobs_list:  # fallback
        jobs_list = fetch_from_csv("jobs_sample.csv")

    return save_jobs_to_mongo(jobs_list)


if __name__ == "__main__":
    print("🔄 Fetching jobs...")
    result = refresh_jobs("Data Scientist", "India", limit=10)
    print(result)
