import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

API_KEY = os.getenv("OPENROUTER_API_KEY")

r = httpx.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
    json={
        "model": "google/gemma-3-4b-it:free",
        "messages": [{"role": "user", "content": "Is this fake news? Government announces tax free india. Reply with JSON only."}],
        "temperature": 0.1
    },
    timeout=30
)
print("STATUS:", r.status_code)
print("FULL RESPONSE:", r.json())