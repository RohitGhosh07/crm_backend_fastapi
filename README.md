# Backend (FastAPI)

This folder contains a minimal FastAPI backend for the SaaS Admin Dashboard. It is configured to run with PostgreSQL (via Docker) and provides a small set of models and CRUD endpoints to get started.

Quick start (using docker-compose from repository root):

```powershell
docker compose up --build
```

The backend will be available at `http://localhost:8000` and the interactive API docs at `http://localhost:8000/docs`.

Customize environment variables by copying `.env.example` to `.env` and editing values.
