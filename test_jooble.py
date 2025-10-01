import os
import requests
from dotenv import load_dotenv

load_dotenv()
JOOBLE_API_KEY = os.getenv("JOOBLE_API_KEY")

url = f"https://jooble.org/api/{JOOBLE_API_KEY}"
payload = {"keywords": "Data Scientist", "location": "India", "page": 1}

response = requests.post(url, json=payload)
print("Status:", response.status_code)
print(response.json())
