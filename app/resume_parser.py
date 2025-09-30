import re
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# ----------------------------
# Rule-based Parser
# ----------------------------
def parse_resume_text(resume_text: str) -> dict:
    """Extracts basic fields from resume text using regex (fast but limited)."""
    parsed_data = {}

    try:
        # Name (first line assumption, skip headers like Resume/CV)
        lines = [l.strip() for l in resume_text.splitlines() if l.strip()]
        parsed_data["Name"] = (
            lines[0]
            if lines and not re.search(r"(resume|curriculum vitae)", lines[0], re.I)
            else None
        )

        # Email
        email_match = re.search(
            r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", resume_text
        )
        parsed_data["Email"] = email_match.group() if email_match else None

        # Phone
        phone_match = re.search(r"\+?\d[\d\s-]{8,}\d", resume_text)
        parsed_data["Phone"] = phone_match.group() if phone_match else None

        # Skills
        skills = re.findall(
            r"\b(Python|Java|C\+\+|SQL|Machine Learning|Deep Learning|AI|Data Science)\b",
            resume_text,
            re.I,
        )
        parsed_data["Skills"] = (
            list(set([s.title() for s in skills])) if skills else []
        )

    except Exception as e:
        parsed_data["Error"] = f"Rule-based parsing failed: {e}"

    return parsed_data


# ----------------------------
# AI-powered Parser (Groq)
# ----------------------------
def ai_parse_resume_text(resume_text: str) -> dict:
    """
    Uses Groq AI API to parse resumes into structured JSON with the same schema
    as the rule-based parser. Requires GROQ_API_KEY env variable.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("⚠️ GROQ_API_KEY not set in environment variables")

    # ✅ Correct Groq endpoint
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    system_prompt = (
        "You are a resume parsing expert. Extract ONLY the following fields "
        "and respond in strict JSON format (no explanations, no markdown):\n"
        "{\n"
        '  "Name": string or null,\n'
        '  "Email": string or null,\n'
        '  "Phone": string or null,\n'
        '  "Skills": list of strings,\n'
        '  "Education": list of strings,\n'
        '  "Experience": list of strings\n'
        "}"
    )

    # ✅ Use a supported model (from list_models.py)
    payload = {
        "model": "llama-3.1-8b-instant",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Resume Text:\n\n{resume_text}"},
        ],
        "temperature": 0.1,
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()

        # Debug: Print raw response (optional, can remove later)
        # print(json.dumps(result, indent=2))

        ai_output = result["choices"][0]["message"]["content"]

        # Convert AI output to dict
        parsed = json.loads(ai_output)

        # Ensure schema consistency (fill missing keys with defaults)
        schema = {
            "Name": None,
            "Email": None,
            "Phone": None,
            "Skills": [],
            "Education": [],
            "Experience": [],
        }
        for key in schema:
            parsed.setdefault(key, schema[key])

        return parsed

    except requests.exceptions.RequestException as e:
        return {"Error": f"API request failed: {e}"}
    except json.JSONDecodeError:
        return {
            "Error": "Failed to decode AI response as JSON",
            "RawOutput": locals().get("ai_output", ""),
        }
    except Exception as e:
        # Debug: show raw response if available
        return {
            "Error": f"Unexpected AI parser error: {e}",
            "RawResponse": locals().get("result", {}),
        }
