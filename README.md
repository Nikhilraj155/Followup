# FollowUpAI 🚀

**FollowUpAI** is a full-stack job application follow-up email automation platform built with **React**, **FastAPI**, **PostgreSQL**, **Celery**, **Redis**, **Gmail OAuth API**, and **LLM AI integration**.

It automatically monitors email thread conversations after sending job applications, detects recruiter/HR replies, cancels follow-up schedules when HR responds, and generates personalized, thread-aware follow-up emails using AI.

---

## 🌟 Key Features

1. **Gmail OAuth 2.0 Integration**: Secure Google authentication and thread-aware email sending (`In-Reply-To`, `References`, `threadId`).
2. **Automated Follow-up Cadence**:
   - Stage 1: 24-hour follow-up delay (default count: 3).
   - Stage 2: 5-day follow-up delay (1 final follow-up).
   - Max follow-up cap (default: 4).
   - Fully configurable per user in Settings.
3. **Pre-flight Reply Detection**: Immediately checks email thread for HR response prior to dispatching any email.
4. **Human Approval Mode**: AI drafts generated and presented in the React UI for review, editing, regeneration, or approval.
5. **AI Service**: LLM API (OpenAI / Gemini) integration with structured output (`should_follow_up`, `subject`, `body`, `reason`) and fallback template engine.
6. **Strict Idempotency**: Atomic guards to prevent duplicate follow-ups or sending after recruiter replies.
7. **Resume Attachment Support**: Supports uploading resume files (PDF/DOCX) when composing applications.
8. **Docker & Docker Compose Ready**: Multi-container setup (`frontend`, `backend`, `postgres`, `redis`, `celery_worker`, `celery_beat`).

---

## 🛠️ Tech Stack

- **Frontend**: React 18 + Vite + Tailwind CSS + React Router + Axios
- **Backend**: Python 3.11+ + FastAPI + Pydantic v2
- **Database & ORM**: PostgreSQL + SQLAlchemy 2.0 + Alembic
- **Background Worker & Broker**: Celery + Redis
- **Authentication**: JWT + OAuth 2.0 + Fernet Token Encryption
- **Containerization**: Docker & Docker Compose

---

## 🚀 Quick Start (Docker Compose)

The simplest way to run the entire application stack:

```bash
docker compose up --build
```

Access the applications:
- **Frontend Dashboard**: `http://localhost:3000`
- **Backend API Docs (Swagger UI)**: `http://localhost:8000/docs`
- **ReDoc API Documentation**: `http://localhost:8000/redoc`

---

## 💻 Local Development Setup

### 1. Backend Setup

```bash
cd backend
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

Run database migrations:
```bash
alembic upgrade head
```

Run Pytest suite:
```bash
python -m pytest
```

Start FastAPI development server:
```bash
uvicorn app.main:app --reload --port 8000
```

Start Celery Worker (in a separate terminal):
```bash
celery -A app.workers.celery_app worker --loglevel=info
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

---

## 🔑 Environment Variables (`.env`)

Copy `.env.example` to `.env` and fill in your credentials:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://postgres:postgres@localhost:5432/followup_db` |
| `REDIS_URL` | Redis URL for Celery broker | `redis://localhost:6379/0` |
| `GOOGLE_CLIENT_ID` | Google OAuth 2.0 Client ID | Required for live Gmail |
| `GOOGLE_CLIENT_SECRET` | Google OAuth 2.0 Client Secret | Required for live Gmail |
| `GOOGLE_REDIRECT_URI` | Google OAuth redirect callback | `http://localhost:8000/api/auth/google/callback` |
| `AI_API_KEY` | OpenAI or Gemini API Key | Required for LLM AI |
| `AI_PROVIDER` | `openai` or `gemini` | `openai` |
| `AI_MODEL` | LLM Model Name | `gpt-4o-mini` |
| `JWT_SECRET` | Secret key for JWT signing | Set custom random string |
| `ENCRYPTION_KEY` | 32-byte Fernet base64 key | Set custom Fernet key |

---

## 📊 Database Schema Summary

- `users`: User profiles and hashed credentials.
- `email_accounts`: Encrypted Gmail OAuth tokens and connected addresses.
- `contacts`: HR/Recruiter contact information.
- `applications`: Job application details, company, job title, status.
- `email_threads`: Provider thread IDs and subjects.
- `emails`: Individual sent/received emails and follow-ups.
- `follow_ups`: Scheduled and generated follow-up records with approval state.
- `automation_settings`: Per-user configurable follow-up rules and delays.

---

## 🧪 Testing

Run backend tests:
```bash
cd backend
python -m pytest
```
Tests cover:
- Authentication & JWT token verification
- Application CRUD & status workflows
- AI Service logic (`HR replied -> should_follow_up = False`, `No reply -> should_follow_up = True`)
- Reply Detection & atomic follow-up cancellation
- Idempotency & duplicate send prevention
