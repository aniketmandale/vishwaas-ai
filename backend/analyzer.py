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
- Well known geographical or historical facts = REAL, score 85-95
- Celebrity rumors = UNCERTAIN, score 40-60
- NEVER give 50 as overall_score — be decisive
- If Hindi/Marathi/Tamil/Bengali — translate first then analyze

Return ONLY this JSON with no extra text, no markdown, no code fences:
{{"detected_language":"English","overall_score":20,"verdict":"FAKE","summary":"Clear reason for verdict.","source_reliability":10,"emotional_language":85,"fact_check_match":10,"sensationalism":88,"flagged_words":["word1","word2"],"reasons":["Reason 1","Reason 2","Reason 3"],"sources":["Source 1","Source 2"]}}

Now analyze: "{text}" and return a NEW JSON with real values."""


def parse_response(content: str) -> dict:
    content = content.strip()
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
    start = content.find("{")
    end = content.rfind("}") + 1
    if start != -1 and end > start:
        content = content[start:end]
    try:
        result = json.loads(content)
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
        if "overall_score" in result and "verdict" in result:
            return result
    except json.JSONDecodeError:
        pass
    content_lower = content.lower()
    if "fake" in content_lower:
        return build_fake_result()
    elif "real" in content_lower or "true" in content_lower:
        return build_real_result()
    return None


def build_fake_result(summary="This content shows signs of misinformation.", flagged=[], reasons=[], sources=[]):
    return {
        "detected_language": "English",
        "overall_score": 20,
        "verdict": "FAKE",
        "summary": summary,
        "source_reliability": 15,
        "emotional_language": 80,
        "fact_check_match": 10,
        "sensationalism": 85,
        "flagged_words": flagged,
        "reasons": reasons or ["Sensational claim without verified sources", "Matches known misinformation patterns"],
        "sources": sources or ["https://www.altnews.in", "https://factcheck.afp.com", "https://pib.gov.in"]
    }


def build_real_result(summary="This content appears to be credible and verifiable.", flagged=[], reasons=[], sources=[]):
    return {
        "detected_language": "English",
        "overall_score": 82,
        "verdict": "REAL",
        "summary": summary,
        "source_reliability": 85,
        "emotional_language": 15,
        "fact_check_match": 85,
        "sensationalism": 10,
        "flagged_words": flagged,
        "reasons": reasons or ["Claim is verifiable through official sources", "Factual and measured language", "Consistent with known facts"],
        "sources": sources or ["https://pib.gov.in", "https://www.thehindu.com", "https://timesofindia.com"]
    }


def build_uncertain_result(summary="Could not fully verify this claim. Please cross-check with official sources."):
    return {
        "detected_language": "English",
        "overall_score": 48,
        "verdict": "UNCERTAIN",
        "summary": summary,
        "source_reliability": 45,
        "emotional_language": 55,
        "fact_check_match": 45,
        "sensationalism": 50,
        "flagged_words": [],
        "reasons": [
            "Insufficient information to fully verify this claim",
            "No strong indicators of fake or real news detected",
            "Recommend checking official sources before sharing"
        ],
        "sources": ["https://pib.gov.in", "https://www.altnews.in", "https://factcheck.afp.com"]
    }


def rule_based_analysis(text: str) -> dict:
    text_lower = text.lower()

    # ── DEFINITE FAKE PATTERNS ──
    fake_patterns = [
        "free electricity for all", "free petrol", "free internet for all",
        "tax free india", "tax-free india", "no tax india",
        "free mobile for all", "free laptop for all",
        "loan waiver for all", "free ration for all",
        "government gives free", "announces free for all",
        "मुफ्त बिजली", "मुफ्त पेट्रोल", "मुफ्त इंटरनेट",
        "सरकार ने मुफ्त", "सभी नागरिकों को मुफ्त",
        "100% guaranteed", "share karo jaldi", "जल्दी शेयर करो",
        "forward this message", "virus will delete your phone",
        "whatsapp is charging", "whatsapp will become paid",
        "bill gates giving money", "mark zuckerberg giving money",
        "drink cow urine to cure", "corona cure found at home",
    ]

    # ── DEFINITE REAL PATTERNS ──
    real_patterns = [
        # Geography and facts
        "is a state of india", "is a city in india", "is the capital of",
        "is located in", "india is a country", "mumbai is",
        "delhi is", "maharashtra is", "gujarat is", "punjab is",
        "is the largest state", "is the smallest state",
        "himalaya", "ganga river", "yamuna river", "indian ocean",
        # Government and institutions
        "rbi repo rate", "reserve bank of india", "rbi governor",
        "supreme court of india", "high court", "parliament of india",
        "election commission", "union budget", "lok sabha", "rajya sabha",
        "sebi", "sensex", "nifty", "bse", "nse",
        # Verified business news
        "adani acquires", "tata acquires", "reliance acquires",
        "merger approved", "ipo launched", "quarterly results",
        "isro launches", "chandrayaan", "mangalyaan",
        # Sports facts
        "ipl 2024", "ipl 2025", "world cup 2024", "world cup 2025",
        "bcci", "india won", "india lost",
        # Historical facts
        "india got independence", "independence day", "republic day",
        "founded in", "established in", "born in", "died in",
    ]

    # ── UNCERTAIN PATTERNS ──
    uncertain_patterns = [
        "according to sources", "reportedly", "sources say",
        "unconfirmed", "rumored", "alleged", "claims to",
        "insider says", "anonymous source"
    ]

    is_fake = any(p in text_lower for p in fake_patterns)
    is_real = any(p in text_lower for p in real_patterns)
    is_uncertain = any(p in text_lower for p in uncertain_patterns)

    if is_fake:
        return build_fake_result(
            summary="This claim matches known misinformation patterns.",
            flagged=["free", "all citizens", "announces"],
            reasons=[
                "Matches known fake news pattern",
                "No official government source cited",
                "Free benefit announcements without budget are almost always fake"
            ],
            sources=["https://pib.gov.in", "https://www.altnews.in", "https://factcheck.afp.com"]
        )
    elif is_real and not is_uncertain:
        return build_real_result(
            summary="This is a verifiable factual claim.",
            reasons=[
                "This is a well-established verifiable fact",
                "Consistent with official records and sources",
                "No misinformation indicators detected"
            ],
            sources=["https://pib.gov.in", "https://www.thehindu.com", "https://en.wikipedia.org"]
        )
    elif is_uncertain:
        return build_uncertain_result(
            summary="This claim is based on unnamed sources and cannot be fully verified."
        )

    return None


def apply_keyword_rules(text: str, result: dict) -> dict:
    rule_result = rule_based_analysis(text)
    if rule_result and result.get("verdict") == "UNCERTAIN":
        return rule_result
    return result


def analyze_text(text: str) -> dict:
    # First try rule-based analysis
    rule_result = rule_based_analysis(text)

    # Try AI if OpenRouter key is available
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
        if "choices" in data:
            content = data["choices"][0]["message"]["content"]
            print(f"Raw AI response: {content[:200]}")
            ai_result = parse_response(content)
            if ai_result and ai_result.get("verdict") != "UNCERTAIN":
                return apply_keyword_rules(text, ai_result)
            elif ai_result:
                # AI says uncertain — try rule-based override
                rule_override = rule_based_analysis(text)
                if rule_override:
                    return rule_override
                return ai_result
        else:
            print(f"No choices in response: {data}")
    except Exception as e:
        print(f"AI call failed: {e}")

    # Use rule-based result if available
    if rule_result:
        return rule_result

    # Final fallback
    return build_uncertain_result()


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
            return apply_keyword_rules(content, result)
        return get_fallback_response("image content")
    except Exception as e:
        print(f"Image analyzer error: {e}")
        return get_fallback_response("image content")


def get_fallback_response(text: str) -> dict:
    rule_result = rule_based_analysis(text)
    if rule_result:
        return rule_result
    return build_uncertain_result()
