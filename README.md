<<<<<<< HEAD
# Vishwaas AI — Fake News Detector for India

> **Team Vishwaas** | Aniket Mandale | AI-Hack @ NareshIT 2026

![Vishwaas AI](https://img.shields.io/badge/Vishwaas_AI-Fake_News_Detector-6c63ff?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.14-blue?style=for-the-badge&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.135-green?style=for-the-badge&logo=fastapi)
![Supabase](https://img.shields.io/badge/Supabase-Database-3ECF8E?style=for-the-badge&logo=supabase)
![OpenRouter](https://img.shields.io/badge/OpenRouter-AI-ff6b6b?style=for-the-badge)

---

## What is Vishwaas AI?

India is the world's largest consumer of misinformation. Every day, millions of fake news articles, fabricated headlines, and doctored screenshots are forwarded on WhatsApp in Hindi, Marathi, Tamil, Bengali, and other regional languages. Ordinary people have no fast, reliable way to verify what is real before sharing it further.

**Vishwaas AI** solves this. Any user can paste a suspicious headline, enter a news URL, or upload a WhatsApp screenshot and receive a detailed AI-powered credibility report in under 5 seconds — in any Indian language.

---

## Live Demo

- **Frontend:** [https://vishwaas-ai.vercel.app](https://vishwaas-ai.vercel.app)
- **Backend API:** [https://vishwaas-ai-api.onrender.com](https://vishwaas-ai-api.onrender.com)
- **API Docs:** [https://vishwaas-ai-api.onrender.com/docs](https://vishwaas-ai-api.onrender.com/docs)

---

## Features

| Feature | Description |
|---|---|
| Text Analysis | Paste any headline or URL for instant analysis |
| Image OCR | Upload WhatsApp screenshots — AI reads and analyzes them |
| Indian Languages | Supports Hindi, Marathi, Tamil, Bengali, Telugu, English |
| Trust Score | Overall credibility score from 0 to 100 |
| Score Breakdown | Source Reliability, Emotional Language, Fact-Check Match, Sensationalism |
| Flagged Words | Specific suspicious words highlighted |
| AI Reasoning | 3-5 clear reasons explaining the verdict |
| Sources Cited | Real web sources used to reach the verdict |
| History | All past checks stored in Supabase database |
| Recently Debunked | Live feed of latest fake news caught |
| 3 Color Themes | Purple, Lilac, Teal — user preference saved |
| PWA Ready | Installable on Android/iPhone like a native app |
| WhatsApp Bot | Coming Soon — forward messages directly to our bot |
| Fully Responsive | Mobile, Tablet, Desktop |

---

## Tech Stack

| Layer | Technology |
|---|---|
| AI Engine | OpenRouter API — google/gemma-3-4b-it:free |
| Image OCR | Gemini Vision via OpenRouter |
| Backend | Python 3.14 + FastAPI |
| Database | Supabase (PostgreSQL) |
| Frontend | HTML5 + CSS3 + Vanilla JavaScript |
| Frontend Deploy | Vercel |
| Backend Deploy | Render |
| PWA | manifest.json |

---

## Project Structure

```
vishwaas-ai/
├── backend/
│   ├── main.py          # FastAPI server — all API endpoints
│   ├── analyzer.py      # AI analysis logic — Gemini prompt engineering
│   ├── database.py      # Supabase database operations
│   ├── requirements.txt # Python dependencies
│   └── .env             # API keys (never committed)
│
├── frontend/
│   ├── index.html       # Landing page
│   ├── result.html      # Analysis result page
│   ├── history.html     # Past checks history page
│   ├── 404.html         # Error page
│   ├── style.css        # All styles — 3 themes, responsive
│   └── manifest.json    # PWA configuration
│
└── README.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/` | Health check |
| GET | `/health` | Server status |
| POST | `/analyze` | Analyze text or URL |
| POST | `/analyze-image` | Analyze WhatsApp screenshot |
| GET | `/recent` | Get recent checks for live feed |
| GET | `/history` | Get all past checks |
| GET | `/stats` | Get FAKE/REAL/UNCERTAIN counts |

---

## How to Run Locally

### Prerequisites
- Python 3.11+
- Git

### 1. Clone the repository
```bash
git clone https://github.com/aniketmandale/vishwaas-ai.git
cd vishwaas-ai
```

### 2. Install dependencies
```bash
pip install -r backend/requirements.txt
```

### 3. Set up environment variables
Create `backend/.env` file:
```
OPENROUTER_API_KEY=your_openrouter_key_here
SUPABASE_URL=your_supabase_url_here
SUPABASE_KEY=your_supabase_anon_key_here
```

### 4. Set up Supabase database
- Go to your Supabase project
- Open SQL Editor
- Run the contents of `supabase_schema.sql`

### 5. Start the backend
```bash
cd vishwaas-ai
python -m uvicorn backend.main:app --reload --port 8000
```

### 6. Start the frontend
```bash
cd frontend
python -m http.server 3000
```

### 7. Open in browser
```
http://localhost:3000
```

---

## How It Works

```
User Input (Text/URL/Image)
        ↓
FastAPI Backend (/analyze)
        ↓
OpenRouter AI (google/gemma-3-4b-it)
        ↓
Structured JSON Response
  - Overall Score (0-100)
  - Verdict (REAL/FAKE/UNCERTAIN)
  - 4 Sub-scores
  - Flagged Words
  - Reasons
  - Sources
        ↓
Save to Supabase Database
        ↓
Display on Result Page
```

---

## Roadmap

- WhatsApp Bot integration via Meta Business API
- Browser extension for one-click fact checking
- Hindi/Regional language UI
- Community fact-checking and voting
- News source credibility database for India
- API for third-party integrations

---

## Team

| Name | Role |
|---|---|
| Aniket Mandale | Solo Developer — Full Stack + AI |

**Hackathon:** AI-Hack @ NareshIT 2026
**Team Name:** Team Vishwaas

---

## License

MIT License — free to use and modify.

---

> *Vishwaas (विश्वास) means "Trust" in Hindi — because every Indian deserves to trust the news they read.*
=======
# vishwaas-ai
Hackathon Projet
>>>>>>> 2c11d84f43f4fbf5d630f0564b354418e4fc7628
