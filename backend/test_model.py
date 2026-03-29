import httpx

API_KEY = "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"

models = [
    "google/gemma-3-4b-it:free",
    "google/gemma-2-9b-it:free",
    "qwen/qwen-2.5-7b-instruct:free",
    "microsoft/phi-3-mini-128k-instruct:free",
    "huggingfaceh4/zephyr-7b-beta:free"
]

for model in models:
    try:
        r = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": "Is 'Government announces tax free india' real or fake news? Reply with only FAKE or REAL"}]
            },
            timeout=20
        )
        data = r.json()
        if "choices" in data:
            print(f"OK - {model}: {data['choices'][0]['message']['content']}")
        else:
            print(f"ERR - {model}: {data.get('error', {}).get('message', 'unknown')}")
    except Exception as e:
        print(f"FAIL - {model}: {e}")