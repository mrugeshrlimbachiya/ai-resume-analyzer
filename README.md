# 🤖 AI Resume Analyzer — Phase 1 Backend

AI-powered resume analysis using **FastAPI** + **Gemini 2.5 Flash** + **SQLite**.
Upload any PDF resume and instantly receive:

- ✅ ATS compatibility score (0–100)
- 💪 Top strengths
- ⚠️ Key weaknesses
- 🔑 Missing keywords
- 🎤 Predicted interview questions

---

## 📁 Project Structure

```
ai-resume-analyzer/
├── app/
│   ├── __init__.py
│   ├── config.py              # Settings via .env
│   ├── database.py            # Async SQLite setup
│   ├── models/
│   │   ├── __init__.py
│   │   ├── resume.py          # ORM model
│   │   └── schemas.py         # Pydantic response schemas
│   ├── routes/
│   │   ├── __init__.py
│   │   └── resume.py          # API endpoints
│   ├── services/
│   │   ├── __init__.py
│   │   └── gemini_service.py  # Gemini 2.5 Flash integration
│   └── utils/
│       ├── __init__.py
│       └── pdf_parser.py      # PDF text extraction (PyMuPDF)
├── uploads/                   # Saved PDF files (auto-created)
├── main.py                    # FastAPI app entry point
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚡ Quick Setup

### Step 1 — Clone & enter directory

```bash
cd ai-resume-analyzer
```

### Step 2 — Create a Python virtual environment

```bash
# macOS / Linux
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### Step 3 — Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4 — Get your free Gemini API key

1. Go to → **https://aistudio.google.com/app/apikey**
2. Sign in with a Google account
3. Click **"Create API Key"**
4. Copy the key

### Step 5 — Configure environment variables

```bash
cp .env.example .env
```

Open `.env` and paste your key:

```env
GEMINI_API_KEY=AIzaSy...your_actual_key_here...
```

### Step 6 — Run the server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

You should see:

```
✅  Database initialized.
🚀  AI Resume Analyzer is ready.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## 📖 API Documentation

Once running, open in browser:

| URL | Description |
|-----|-------------|
| http://localhost:8000/docs | Swagger UI (interactive) |
| http://localhost:8000/redoc | ReDoc documentation |
| http://localhost:8000/health | Health check |

---

## 🧪 Testing

### Option A — Swagger UI (Easiest)

1. Open **http://localhost:8000/docs**
2. Click `POST /api/v1/resume/analyze`
3. Click **"Try it out"**
4. Upload any PDF resume
5. Click **Execute**

---

### Option B — curl (Terminal)

```bash
curl -X POST "http://localhost:8000/api/v1/resume/analyze" \
  -H "accept: application/json" \
  -F "file=@/path/to/your/resume.pdf"
```

**Example with a real path:**
```bash
curl -X POST "http://localhost:8000/api/v1/resume/analyze" \
  -H "accept: application/json" \
  -F "file=@resume.pdf"
```

---

### Option C — Postman

1. Create a new **POST** request
2. URL: `http://localhost:8000/api/v1/resume/analyze`
3. Go to **Body** tab → select **form-data**
4. Add key: `file` | Type: **File** | Value: select your `.pdf`
5. Click **Send**

---

### Option D — Python script

```python
import requests

with open("resume.pdf", "rb") as f:
    response = requests.post(
        "http://localhost:8000/api/v1/resume/analyze",
        files={"file": ("resume.pdf", f, "application/pdf")},
    )

print(response.json())
```

---

## 📤 Sample Response

```json
{
  "message": "Resume analyzed successfully.",
  "resume_id": 1,
  "filename": "john_doe_resume.pdf",
  "analysis": {
    "id": 1,
    "filename": "john_doe_resume.pdf",
    "ats_score": 74.0,
    "strengths": [
      "Strong technical skills section with relevant technologies",
      "Quantified achievements with specific metrics",
      "Clear chronological work history",
      "Relevant educational background",
      "Good use of action verbs"
    ],
    "weaknesses": [
      "Missing a professional summary/objective section",
      "No LinkedIn or GitHub profile links",
      "Some job descriptions lack measurable impact",
      "Skills section could be more specific",
      "No certifications listed"
    ],
    "missing_keywords": [
      "Agile", "Scrum", "CI/CD", "Docker", "Kubernetes",
      "REST API", "Microservices", "Cloud (AWS/GCP/Azure)"
    ],
    "interview_questions": [
      "Can you walk me through a challenging project you led?",
      "How do you approach debugging a production issue under pressure?",
      "Describe your experience with agile methodologies.",
      "How have you improved system performance in past roles?",
      "Tell me about a time you disagreed with your team and how you handled it.",
      "What's your process for code reviews?",
      "How do you stay up-to-date with new technologies?"
    ],
    "status": "analyzed",
    "created_at": "2024-12-01T10:30:00"
  }
}
```

---

## 🔌 All Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Welcome message |
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/resume/analyze` | Upload & analyze resume |
| `GET` | `/api/v1/resume/{id}` | Get analysis by ID |
| `GET` | `/api/v1/resume/` | List all analyses |

---

## 🚨 Troubleshooting

| Problem | Solution |
|---------|----------|
| `GEMINI_API_KEY not set` | Make sure `.env` file exists and has your key |
| `No extractable text` | PDF might be a scanned image — use a text-based PDF |
| `File too large` | Default limit is 10 MB; change `MAX_FILE_SIZE_MB` in `.env` |
| `502 AI analysis failed` | Check Gemini API key validity at aistudio.google.com |
| `Port already in use` | Run on different port: `uvicorn main:app --port 8001` |

---

## 🔒 .env Reference

```env
GEMINI_API_KEY=your_key_here       # Required
APP_NAME=AI Resume Analyzer        # Optional
DEBUG=True                         # Set False in production
MAX_FILE_SIZE_MB=10                # Max upload size
UPLOAD_DIR=uploads                 # Where PDFs are stored
DATABASE_URL=sqlite+aiosqlite:///./resume_analyzer.db
```

---

## ✅ Phase 1 Complete. Ready for Phase 2 (Frontend).
