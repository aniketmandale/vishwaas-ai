import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

key = os.getenv("OPENROUTER_API_KEY")
print(f"Key loaded: {key[:20] if key else 'NONE'}")
print(f"Key length: {len(key) if key else 0}")

r = httpx.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    json={"model": "google/gemma-3-4b-it:free", "messages": [{"role": "user", "content": "Say hello"}]},
    timeout=15
)
print(r.json())