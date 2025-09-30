from app.resume_parser import parse_resume_text, ai_parse_resume_text
import os
import json

# Sample resume text
sample_resume = """
John Doe
Email: john.doe@example.com
Phone: +1 987-654-3210

Education:
B.Tech in Computer Science
M.Tech in Artificial Intelligence

Experience:
3 years as Software Engineer at ABC Corp
2 years as Data Scientist at XYZ Inc

Skills:
Python, Java, Machine Learning, SQL, Deep Learning
"""

print("=== Rule-based Parser ===")
rule_based_result = parse_resume_text(sample_resume)
print(json.dumps(rule_based_result, indent=2))

print("\n=== AI-powered Parser ===")
if not os.getenv("GROQ_API_KEY"):
    print("⚠️ Skipping AI test: GROQ_API_KEY not set in environment variables.")
else:
    ai_result = ai_parse_resume_text(sample_resume)
    print(json.dumps(ai_result, indent=2))
