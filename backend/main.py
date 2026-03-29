import sys
import os
from pathlib import Path
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from analyzer import analyze_text, analyze_image
from database import save_check, get_recent_checks, get_all_checks, get_stats
import uvicorn

app = FastAPI(
    title="Vishwaas AI API",
    description="AI-powered fake news detector for India",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class TextRequest(BaseModel):
    text: str
    input_type: str = "text"
    device_id: str = "anonymous"


@app.get("/")
def root():
    return {
        "name": "Vishwaas AI",
        "status": "running",
        "version": "1.0.0",
        "message": "API is live"
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze")
async def analyze(request: TextRequest):
    if not request.text or len(request.text.strip()) < 5:
        raise HTTPException(status_code=400, detail="Text is too short.")
    if len(request.text) > 2000:
        raise HTTPException(status_code=400, detail="Text is too long. Max 2000 characters.")

    result = analyze_text(request.text.strip())

    try:
        save_check(
            input_text=request.text.strip(),
            input_type=request.input_type,
            result=result,
            device_id=request.device_id
        )
    except Exception as e:
        print(f"Save error (non-critical): {e}")

    return result


@app.post("/analyze-image")
async def analyze_image_endpoint(
    file: UploadFile = File(...),
    device_id: str = Query(default="anonymous")
):
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="Only JPEG and PNG images are allowed.")

    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="Image too large. Max 5MB.")

    result = analyze_image(contents, file.filename)
    result["input_type"] = "image"

    try:
        save_check(
            input_text=f"[Image: {file.filename}]",
            input_type="image",
            result=result,
            device_id=device_id
        )
    except Exception as e:
        print(f"Save error (non-critical): {e}")

    return result


@app.get("/history")
def history(
    limit: int = 50,
    device_id: str = Query(default=None)
):
    checks = get_all_checks(limit=limit, device_id=device_id)
    return {"checks": checks}


@app.get("/recent")
def recent(limit: int = 10):
    checks = get_recent_checks(limit=limit)
    return {"checks": checks}


@app.get("/stats")
def stats(device_id: str = Query(default=None)):
    return get_stats(device_id=device_id)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
