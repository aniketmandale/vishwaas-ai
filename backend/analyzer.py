import json
import os
import base64
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai

# Load from backend/.env for local, os.environ for Render
load_dotenv(dotenv_path=Path(__file__).parent / ".env")

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")


def get_model():
    key = os.environ.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=key)
    return genai.GenerativeModel("gemini-2.0-flash-lite")


def build_prompt(text: str) -> str:
    return f"""You are Vishwaas AI, a strict Indian fake news detector. Analyze this news and give a DECISIVE verdict.

NEWS: "{text}"

STRICT RULES:
- "Government announces free X for all" = FAKE, score 10-25
- "Tax free India/country" claims = FAKE, score 10-20
- Sensational claims without source = FAKE, score 15-35
- Verified official government news = REAL, score 75-95
- Celebrity rumors = UNCERTAIN, score 40-60
- NEVER give 50 as overall_score — be decisive
- If Hindi/Marathi/Tamil/Bengali — translate first then analyze

Return ONLY this JSON with no extra text, no markdown, no code fences:
{{"detected_language":"English","overall_score":20,"verdict":"FAKE","summary":"Clear reason for verdict.","source_reliability":10,"emotional_language":85,"fact_check_match":10,"sensationalism":88,"flagged_words":["word1","word2"],"reasons":["Reason 1","Reason 2","Reason 3"],"sources":["Source 1","Source 2"]}}

Now analyze: "{text}" and return a NEW JSON with real values."""


def parse_response(content: str) -> dict:
    content = content.strip()

    # Strip markdown fences
    if "```" in content:
        parts = content.split("```")
        for part in parts:
            part = part.strip()
            if part.startswith("json"):
                part = part[4:].strip()
            if part.startswith("{"):
                content = part
                break

    content = content.strip()

    # Find JSON object in response
    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end > start:
        content = content[start:end]

    try:
        result = json.loads(content)
        if "overall_score" in result and "verdict" in result:
            return result
    except json.JSONDecodeError:
        pass

    # Keyword fallback
    content_lower = content.lower()
    if "fake" in content_lower:
        return {
            "detected_language": "English",
            "overall_score": 20,
            "verdict": "FAKE",
            "summary": "This content shows signs of misinformation.",
            "source_reliability": 15,
            "emotional_language": 80,
            "fact_check_match": 10,
            "sensationalism": 85,
            "flagged_words": [],
            "reasons": ["Content identified as potentially fake", "Sensational claims without verified sources"],
            "sources": []
        }
    elif "real" in content_lower or "true" in content_lower:
        return {
            "detected_language": "English",
            "overall_score": 80,
            "verdict": "REAL",
            "summary": "This content appears to be credible.",
            "source_reliability": 85,
            "emotional_language": 20,
            "fact_check_match": 85,
            "sensationalism": 15,
            "flagged_words": [],
            "reasons": ["Content appears credible", "Matches known facts"],
            "sources": []
        }

    return None


def apply_keyword_rules(text: str, result: dict) -> dict:
    text_lower = text.lower()

    fake_patterns = [
        "free electricity", "free petrol", "free internet", "free mobile",
        "muft bijli", "muft petrol", "मुफ्त बिजली", "मुफ्त पेट्रोल",
        "tax free india", "no tax", "government gives free",
        "सरकार ने मुफ्त", "सभी नागरिकों को मुफ्त",
        "free for all citizens", "announces free",
        "100% guaranteed", "share karo", "जल्दी शेयर करो",
    ]

    strong_fake = any(p in text_lower for p in fake_patterns)

    if strong_fake and result.get("verdict") == "UNCERTAIN":
        result["verdict"] = "FAKE"
        result["overall_score"] = min(result.get("overall_score", 50), 30)
        result["summary"] = "This claim matches common misinformation patterns — free benefit announcements without official sources are almost always fake."
        result["reasons"].insert(0, "Matches known fake news pattern — unverified free benefit claim")
        result["flagged_words"] = list(set(result.get("flagged_words", []) + ["free", "all citizens", "government announces"]))

    return result


def analyze_text(text: str) -> dict:
    try:
        model = get_model()
        response = model.generate_content(build_prompt(text))
        content = response.text
        print(f"Raw Gemini response: {content[:200]}")

        result = parse_response(content)
        if result:
            result = apply_keyword_rules(text, result)
            return result

        return get_fallback_response(text)

    except Exception as e:
        print(f"Analyzer error: {e}")
        return get_fallback_response(text)


def analyze_image(image_bytes: bytes, filename: str) -> dict:
    try:
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        media_type = "image/png" if filename.lower().endswith(".png") else "image/jpeg"

        model = get_model()
        import PIL.Image
        import io
        image = PIL.Image.open(io.BytesIO(image_bytes))

        prompt = f"Extract all text from this WhatsApp screenshot or news image. Then analyze if it is fake news. {build_prompt('[extracted text from image]')}"
        response = model.generate_content([prompt, image])
        content = response.text

        result = parse_response(content)
        if result:
            result["input_type"] = "image"
            result = apply_keyword_rules(content, result)
            return result

        return get_fallback_response("image content")

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
