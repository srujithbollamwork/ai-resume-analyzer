import os
import requests
import json

def ai_resume_feedback(resume_text: str, job_description: str = None):
    """
    Provides feedback on resume strengths, missing skills, and job match explanation.
    If job_description is provided, feedback is tailored to that job.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY not set"}

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    system_prompt = "You are an AI career coach. Provide feedback in JSON format only."
    user_prompt = {
        "resume": resume_text,
        "job": job_description or "N/A"
    }

    payload = {
        "model": "llama-3.1-8b-instant",  # ✅ correct Groq model
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": json.dumps(user_prompt)}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        return json.loads(result["choices"][0]["message"]["content"])
    except Exception as e:
        return {"error": str(e)}
