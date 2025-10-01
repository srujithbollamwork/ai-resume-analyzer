from db_utils import get_jobs
import json

# Fetch 5 jobs
jobs = get_jobs(limit=5)

print("=== Sample Jobs ===")
print(json.dumps(jobs, indent=2))
