# AI Smart Education Assistant

An AI-first learning platform that will turn uploaded study material into grounded answers, summaries, quizzes, flashcards, and personalised study plans.

## Current phase — foundation

This first runnable phase provides:

- responsive landing page and authenticated dashboard shell
- register, login, JWT session, protected profile endpoint
- FastAPI application with Swagger documentation at `/docs`
- clean module boundaries ready for MongoDB, ChromaDB, uploads, and AI services

> The Phase 1 user repository is intentionally in memory so the application runs before MongoDB is configured. Accounts disappear when the server restarts. MongoDB persistence is the next phase.

## Project structure

```text
backend/app/
  api/routes/       # HTTP endpoints
  core/             # configuration and security
  schemas/          # request/response contracts
  services/         # application services and repositories
frontend/           # static, deployable vanilla HTML/CSS/JS client
```

## Run locally

1. Create and activate a virtual environment:

   ```powershell
   cd backend
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```

2. Start the API:

   ```powershell
   uvicorn app.main:app --reload
   ```

3. Serve `frontend` with a static server, for example VS Code Live Server, then open its local URL. The default API URL is `http://127.0.0.1:8000/api`.

## API (Phase 1)

| Method | Endpoint | Purpose |
| --- | --- | --- |
| GET | `/api/health` | Health check |
| POST | `/api/auth/register` | Create account and issue JWT |
| POST | `/api/auth/login` | Log in and issue JWT |
| GET | `/api/auth/profile` | Get signed-in user |

## Planned phases

1. Foundation and authentication — complete
2. MongoDB persistence, uploads, validation, and document metadata
3. Extraction, chunking, embeddings, ChromaDB, and cited RAG chat
4. Quiz, flashcards, study planner, image OCR, and voice workflows
5. History, progress analytics, tests, deployment, and final documentation

## Environment variables

Copy `backend/.env.example` to `backend/.env`. Never commit API keys or production secrets.

## Tech stack

FastAPI, Python, MongoDB Atlas, ChromaDB, OpenAI, vanilla HTML/CSS/JavaScript, and Vercel/Render deployment targets.
