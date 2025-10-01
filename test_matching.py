from app.matching_engine import match_resume_to_jobs
import json

# A fake resume text for testing
sample_resume = """
John Doe
Email: john.doe@example.com
Phone: +1 987-654-3210

Education:
B.Tech in Computer Science

Experience:
3 years as Software Engineer at ABC Corp
2 years as Data Scientist at XYZ Inc

Skills:
Python, Java, Machine Learning, SQL, Deep Learning
"""

print("=== Testing Job Matching Engine ===")

matches = match_resume_to_jobs(sample_resume, top_n=5)

if matches:
    print(f"✅ Found {len(matches)} matching jobs")
    print(json.dumps(matches, indent=2))
else:
    print("⚠️ No matches found. Did you import jobs into MongoDB?")
