# app/ai_assistant.py
import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

def ai_resume_feedback(resume_text: str, job_description: str = None) -> dict:
    """
    Provides AI-powered feedback on a resume.
    If job_description is provided, it will give tailored advice.
    Uses Groq API (Mixtral or LLaMA) to analyze.
    """

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return {"error": "GROQ_API_KEY not set in environment variables"}

    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    system_prompt = (
        "You are an AI resume coach. Analyze resumes and provide feedback.\n"
        "Give JSON output with fields:\n"
        "{\n"
        "  'strengths': [list of strings],\n"
        "  'weaknesses': [list of strings],\n"
        "  'missing_skills': [list of strings],\n"
        "  'suggestions': [list of strings]\n"
        "}\n"
    )

    user_prompt = f"Resume:\n{resume_text}\n"
    if job_description:
        user_prompt += f"\nTarget Job Description:\n{job_description}"

    payload = {
        "model": "llama-3.1-8b-instant",  # ✅ pick one from your Groq models list
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        ai_output = result["choices"][0]["message"]["content"]

        return json.loads(ai_output)

    except requests.exceptions.RequestException as e:
        return {"error": f"API request failed: {e}"}
    except json.JSONDecodeError:
        return {"error": "Failed to parse AI response as JSON"}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}
