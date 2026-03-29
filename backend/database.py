import httpx
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).parent / ".env")

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
    "Prefer": "return=representation"
}


def save_check(input_text, input_type, result, device_id="anonymous"):
    try:
        payload = {
            "input_text": input_text[:500],
            "input_type": input_type,
            "device_id": device_id,
            "detected_language": result.get("detected_language", "Unknown"),
            "overall_score": result.get("overall_score", 50),
            "verdict": result.get("verdict", "UNCERTAIN"),
            "summary": result.get("summary", ""),
            "source_reliability": result.get("source_reliability", 50),
            "emotional_language": result.get("emotional_language", 50),
            "fact_check_match": result.get("fact_check_match", 50),
            "sensationalism": result.get("sensationalism", 50),
            "flagged_words": result.get("flagged_words", []),
            "reasons": result.get("reasons", []),
            "sources": result.get("sources", [])
        }
        response = httpx.post(
            f"{SUPABASE_URL}/rest/v1/checks",
            headers=HEADERS,
            json=payload,
            timeout=10.0
        )
        if response.status_code in [200, 201]:
            return response.json()
        return {}
    except Exception as e:
        print(f"Database error: {e}")
        return {}


def get_recent_checks(limit=10):
    try:
        response = httpx.get(
            f"{SUPABASE_URL}/rest/v1/checks",
            headers=HEADERS,
            params={
                "select": "id,input_text,verdict,overall_score,detected_language,created_at",
                "order": "created_at.desc",
                "limit": limit
            },
            timeout=10.0
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Database fetch error: {e}")
        return []


def get_all_checks(limit=50, device_id=None):
    try:
        params = {
            "select": "*",
            "order": "created_at.desc",
            "limit": limit
        }
        if device_id:
            params["device_id"] = f"eq.{device_id}"
        response = httpx.get(
            f"{SUPABASE_URL}/rest/v1/checks",
            headers=HEADERS,
            params=params,
            timeout=10.0
        )
        if response.status_code == 200:
            return response.json()
        return []
    except Exception as e:
        print(f"Database fetch error: {e}")
        return []


def get_stats(device_id=None):
    try:
        params = {"select": "verdict"}
        if device_id:
            params["device_id"] = f"eq.{device_id}"
        response = httpx.get(
            f"{SUPABASE_URL}/rest/v1/checks",
            headers=HEADERS,
            params=params,
            timeout=10.0
        )
        if response.status_code == 200:
            data = response.json()
            total = len(data)
            fake = len([x for x in data if x["verdict"] == "FAKE"])
            real = len([x for x in data if x["verdict"] == "REAL"])
            uncertain = len([x for x in data if x["verdict"] == "UNCERTAIN"])
            return {"total": total, "fake": fake, "real": real, "uncertain": uncertain}
        return {"total": 0, "fake": 0, "real": 0, "uncertain": 0}
    except Exception as e:
        print(f"Stats error: {e}")
        return {"total": 0, "fake": 0, "real": 0, "uncertain": 0}
