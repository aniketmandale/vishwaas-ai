import httpx
import json
import os
import base64
from dotenv import load_dotenv

from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = "google/gemma-3-4b-it:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://vishwaas-ai.vercel.app",
    "X-Title": "Vishwaas AI"
}


def build_prompt(text: str) -> str:
    return f"""You are Vishwaas AI, an expert fake news detector for India. Analyze the following news content and respond ONLY with a valid JSON object.

NEWS CONTENT: "{text}"

Instructions:
- Detect the language (English, Hindi, Marathi, Tamil, Bengali, Telugu, etc.)
- If not in English, translate and analyze it
- Score each dimension from 0 to 100
- For overall_score: 0-40 = FAKE, 41-69 = UNCERTAIN, 70-100 = REAL
- Find specific words that are sensationalist or suspicious
- Give 3-5 clear reasons for your verdict
- List real sources that can verify this claim

Respond ONLY with this exact JSON format, no other text:
{{
    "detected_language": "English",
    "overall_score": 75,
    "verdict": "REAL",
    "summary": "One sentence plain English explanation of verdict",
    "source_reliability": 80,
    "emotional_language": 30,
    "fact_check_match": 70,
    "sensationalism": 25,
    "flagged_words": ["word1", "word2", "word3"],
    "reasons": [
        "Reason 1 explaining the verdict",
        "Reason 2 explaining the verdict",
        "Reason 3 explaining the verdict"
    ],
    "sources": [
        "Source 1 name or URL",
        "Source 2 name or URL"
    ]
}}"""


def analyze_text(text: str) -> dict:
    try:
        response = httpx.post(
            OPENROUTER_URL,
            headers=HEADERS,
            json={
                "model": OPENROUTER_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": build_prompt(text)
                    }
                ],
                "temperature": 0.3
            },
            timeout=30.0
        )

        data = response.json()

        if "choices" not in data:
            return get_fallback_response(text)

        content = data["choices"][0]["message"]["content"]

        # Clean the response - remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)
        return result

    except Exception as e:
        print(f"Analyzer error: {e}")
        return get_fallback_response(text)


def analyze_image(image_bytes: bytes, filename: str) -> dict:
    try:
        # Convert image to base64
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        # Determine media type
        if filename.lower().endswith(".png"):
            media_type = "image/png"
        elif filename.lower().endswith(".jpg") or filename.lower().endswith(".jpeg"):
            media_type = "image/jpeg"
        else:
            media_type = "image/jpeg"

        response = httpx.post(
            OPENROUTER_URL,
            headers=HEADERS,
            json={
                "model": "google/gemma-3-12b-it:free",
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{media_type};base64,{image_b64}"
                                }
                            },
                            {
                                "type": "text",
                                "content": "Extract all text from this WhatsApp screenshot or news image. Then " + build_prompt("[extracted text from image]")
                            }
                        ]
                    }
                ],
                "temperature": 0.3
            },
            timeout=45.0
        )

        data = response.json()

        if "choices" not in data:
            return get_fallback_response("image content")

        content = data["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith("```"):
            content = content.split("```")[1]
            if content.startswith("json"):
                content = content[4:]
        content = content.strip()

        result = json.loads(content)
        result["input_type"] = "image"
        return result

    except Exception as e:
        print(f"Image analyzer error: {e}")
        return get_fallback_response("image content")


def get_fallback_response(text: str) -> dict:
    return {
        "detected_language": "Unknown",
        "overall_score": 50,
        "verdict": "UNCERTAIN",
        "summary": "Could not analyze this content at the moment. Please try again.",
        "source_reliability": 50,
        "emotional_language": 50,
        "fact_check_match": 50,
        "sensationalism": 50,
        "flagged_words": [],
        "reasons": [
            "Analysis service is temporarily unavailable",
            "Please try again in a few moments",
            "If the problem persists, try rephrasing the input"
        ],
        "sources": []
    }
