# Developer Setup Guide

This guide describes how to configure, run, and test the **MarineDebris-Sonar-AI** monorepo locally and via Docker.

---

## 1. Prerequisites

- **Python:** 3.10 or 3.11
- **Node.js:** 18+ or 20+ (with `npm`)
- **Docker & Docker Compose:** Optional for local development, recommended for full-stack runs
- **PostgreSQL 16 + PostGIS:** (If running locally without Docker)
- **Redis 7.x:** (If running locally without Docker)

---

## 2. Quickstart with Docker Compose

1. Copy the environment configuration template:
   ```bash
   cp .env.example .env
   ```

2. Start all services (PostgreSQL, Redis, FastAPI backend, Celery worker, and React frontend):
   ```bash
   docker compose up --build
   ```

3. Access the services:
   - **Frontend UI:** `http://localhost:3000`
   - **FastAPI OpenAPI Docs:** `http://localhost:8000/docs`
   - **Health Check:** `http://localhost:8000/api/v1/health`

---

## 3. Local Development Setup (Without Docker)

### 3.1 Backend Setup

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   # On Windows (PowerShell):
   .\.venv\Scripts\Activate.ps1
   # On Linux/macOS:
   source .venv/bin/activate
   ```

2. Install Python dependencies:
   ```bash
   pip install -r backend/requirements.txt
   ```

3. Run database migrations:
   ```bash
   alembic upgrade head
   ```

4. Start the FastAPI development server:
   ```bash
   uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
   ```

5. (Optional) Start the Celery worker in a separate terminal:
   ```bash
   celery -A backend.celery_app.celery_app worker --loglevel=info
   ```

### 3.2 Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install Node dependencies:
   ```bash
   npm install
   ```

3. Start Vite development server:
   ```bash
   npm run dev
   ```

4. Build frontend for production verification:
   ```bash
   npm run build
   ```

---

## 4. Running Tests

### Backend Unit & Integration Tests

Run the pytest suite:
```bash
pytest tests/backend -v
```

### Celery Eager Mode (for headless testing)

Set `CELERY_TASK_ALWAYS_EAGER=true` in `.env` or during test runs to execute background tasks synchronously in-process without requiring a running Celery daemon.
