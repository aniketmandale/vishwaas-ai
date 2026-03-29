import httpx

OPENROUTER_API_KEY = "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"

response = httpx.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    },
    json={
        "model": "mistralai/mistral-7b-instruct:free",
        "messages": [
            {"role": "user", "content": "Say exactly: Vishwaas AI is ready to fight fake news!"}
        ]
    }
)

data = response.json()
print(data)