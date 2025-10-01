# test_imports.py
try:
    from app import main, matching_engine, resume_parser, mongodb_config, ai_assistant, job_fetcher
    print("✅ All modules imported successfully!")
except Exception as e:
    print(f"❌ Import failed: {e}")
