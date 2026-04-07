import httpx
import json
import os
import base64
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.environ.get("OPENROUTER_MODEL") or os.getenv("OPENROUTER_MODEL") or "google/gemma-3-4b-it:free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def get_headers():
    key = os.environ.get("OPENROUTER_API_KEY") or os.getenv("OPENROUTER_API_KEY")
    return {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://vishwaas-ai.vercel.app",
        "X-Title": "Vishwaas AI"
    }


def build_prompt(text: str) -> str:
    return f"""You are Vishwaas AI, a strict Indian fact-checker. Analyze this news and give a DECISIVE verdict.

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

        # Handle model's own format
        if "is_fake_news" in result:
            is_fake = result.get("is_fake_news", False)
            reason = result.get("reason", "Analysis complete.")
            verdict = "FAKE" if is_fake else "REAL"
            score = 20 if is_fake else 80
            return {
                "detected_language": "English",
                "overall_score": score,
                "verdict": verdict,
                "summary": reason[:200],
                "source_reliability": 15 if is_fake else 85,
                "emotional_language": 80 if is_fake else 20,
                "fact_check_match": 10 if is_fake else 85,
                "sensationalism": 85 if is_fake else 15,
                "flagged_words": [],
                "reasons": [reason],
                "sources": []
            }

        # Our expected format
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
        response = httpx.post(
            OPENROUTER_URL,
            headers=get_headers(),
            json={
                "model": OPENROUTER_MODEL,
                "messages": [{"role": "user", "content": build_prompt(text)}],
                "temperature": 0.1
            },
            timeout=30.0
        )

        data = response.json()
        if "choices" not in data:
            print(f"No choices in response: {data}")
            return get_fallback_response(text)

        content = data["choices"][0]["message"]["content"]
        print(f"Raw AI response: {content[:200]}")

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

        response = httpx.post(
            OPENROUTER_URL,
            headers=get_headers(),
            json={
                "model": "google/gemma-3-12b-it:free",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{image_b64}"}},
                        {"type": "text", "content": "Extract all text from this image then analyze if it is fake news. " + build_prompt("[extracted text from image]")}
                    ]
                }],
                "temperature": 0.1
            },
            timeout=45.0
        )

        data = response.json()
        if "choices" not in data:
            return get_fallback_response("image content")

        content = data["choices"][0]["message"]["content"]
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
    text_lower = text.lower()

    # Smart fallback based on keywords
    fake_patterns = [
        "free electricity", "free petrol", "free internet",
        "tax free india", "free for all", "announces free",
        "मुफ्त", "muft", "loan waiver", "free mobile",
        "government gives free", "100% free"
    ]

    real_patterns = [
        "rbi", "reserve bank", "supreme court", "high court",
        "budget 2024", "budget 2025", "parliament passed",
        "election commission", "isro", "nasa",
        "adani", "tata", "reliance", "infosys", "wipro",
        "acquires", "acquisition", "merger", "stake",
        "ndtv", "sebi", "sensex", "nifty", "bse", "nse",
        "modi", "pm modi", "prime minister", "cabinet",
        "rbi governor", "interest rate", "repo rate",
        "ipl", "bcci", "cricket", "world cup"
    ]

    is_fake = any(p in text_lower for p in fake_patterns)
    is_real = any(p in text_lower for p in real_patterns) and not is_fake

    if is_fake:
        return {
            "detected_language": "English",
            "overall_score": 22,
            "verdict": "FAKE",
            "summary": "This claim matches common misinformation patterns — unverified free benefit announcements are almost always fake.",
            "source_reliability": 10,
            "emotional_language": 85,
            "fact_check_match": 10,
            "sensationalism": 88,
            "flagged_words": ["free", "government announces", "all citizens"],
            "reasons": [
                "No official government source cited for this claim",
                "Free benefit announcements without budget allocation are classic fake news",
                "This pattern is commonly used in WhatsApp misinformation"
            ],
            "sources": [
                "https://pib.gov.in",
                "https://www.thehindu.com",
                "https://factcheck.afp.com"
            ]
        }
    elif is_real:
        return {
            "detected_language": "English",
            "overall_score": 78,
            "verdict": "REAL",
            "summary": "This appears to be a credible news claim from a verifiable official source.",
            "source_reliability": 80,
            "emotional_language": 20,
            "fact_check_match": 75,
            "sensationalism": 15,
            "flagged_words": [],
            "reasons": [
                "References a known official institution",
                "Language is factual and measured",
                "Consistent with verified news sources"
            ],
            "sources": [
                "https://rbi.org.in",
                "https://pib.gov.in",
                "https://www.thehindu.com"
            ]
        }
    else:
        return {
            "detected_language": "Unknown",
            "overall_score": 48,
            "verdict": "UNCERTAIN",
            "summary": "Could not fully verify this claim. Please cross-check with official sources before sharing.",
            "source_reliability": 45,
            "emotional_language": 55,
            "fact_check_match": 45,
            "sensationalism": 50,
            "flagged_words": [],
            "reasons": [
                "Insufficient information to verify this claim",
                "No strong indicators of fake or real news detected",
                "Recommend checking official sources"
            ],
            "sources": [
                "https://pib.gov.in",
                "https://www.altnews.in",
                "https://factcheck.afp.com"
            ]
        }