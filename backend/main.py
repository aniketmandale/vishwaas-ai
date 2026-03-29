from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from analyzer import analyze_text, analyze_image
from database import save_check, get_recent_checks, get_all_checks, get_stats
import uvicorn

app = FastAPI(
    title="Vishwaas AI API",
    description="AI-powered fake news detector for India",
    version="1.0.0"
)

# CORS - allows frontend to talk to backend
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
        raise HTTPException(
            status_code=400,
            detail="Text is too short. Please enter a valid headline or URL."
        )

    if len(request.text) > 2000:
        raise HTTPException(
            status_code=400,
            detail="Text is too long. Please enter text under 2000 characters."
        )

    # Run AI analysis
    result = analyze_text(request.text.strip())

    # Save to database (non-blocking)
    try:
        save_check(
            input_text=request.text.strip(),
            input_type=request.input_type,
            result=result
        )
    except Exception as e:
        print(f"Save error (non-critical): {e}")

    return result


@app.post("/analyze-image")
async def analyze_image_endpoint(file: UploadFile = File(...)):
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/jpg", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=400,
            detail="Only JPEG and PNG images are allowed."
        )

    # Validate file size (max 5MB)
    contents = await file.read()
    if len(contents) > 5 * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail="Image too large. Maximum size is 5MB."
        )

    # Run AI analysis on image
    result = analyze_image(contents, file.filename)
    result["input_type"] = "image"

    # Save to database
    try:
        save_check(
            input_text=f"[Image: {file.filename}]",
            input_type="image",
            result=result
        )
    except Exception as e:
        print(f"Save error (non-critical): {e}")

    return result


@app.get("/history")
def history(limit: int = 50):
    checks = get_all_checks(limit=limit)
    return {"checks": checks}


@app.get("/recent")
def recent(limit: int = 10):
    checks = get_recent_checks(limit=limit)
    return {"checks": checks}


@app.get("/stats")
def stats():
    return get_stats()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
