import pandas as pd
from pymongo import UpdateOne
from app.mongodb_config import jobs_collection  # ✅ use central Mongo config
import re

def clean_col_names(df):
    """Normalize CSV column names to snake_case."""
    new_cols = []
    for col in df.columns:
        new_col = re.sub(r'[^A-Za-z0-9_]+', '', col.lower().strip().replace(' ', '_'))
        new_cols.append(new_col)
    df.columns = new_cols
    return df


def import_jobs_from_csv(csv_path="jobs_sample.csv"):
    """Import jobs into MongoDB from a CSV file."""
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
    if not records:
        return {"error": "⚠️ No valid records found in CSV."}

    jobs_collection.drop()  # ⚠️ resets jobs collection before import
    print("Dropped existing 'jobs' collection.")

    jobs_collection.create_index([("title", 1), ("company", 1)], unique=True, sparse=True)
    print("Created unique sparse index on (title, company).")

    ops = [
        UpdateOne(
            {"title": record["title"], "company": record["company"]},
            {"$set": record},
            upsert=True,
        )
        for record in records
        if record.get("title") and record.get("company")
    ]

    if not ops:
        return {"error": "⚠️ No valid operations created."}

    result = jobs_collection.bulk_write(ops)
    return {
        "inserted": result.upserted_count,
        "updated": result.modified_count,
        "message": "✅ Jobs imported successfully from CSV."
    }


if __name__ == "__main__":
    print("📂 Importing jobs from CSV...")
    result = import_jobs_from_csv("jobs_sample.csv")
    print(result)
