import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db import engine, Base
from .routers import clients, auth

app = FastAPI(title="SaaS Admin Dashboard - Backend")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins for security
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)


@app.on_event("startup")
def on_startup():
    # Create database tables (for development/demo). In production, use migrations.
    Base.metadata.create_all(bind=engine)


app.include_router(auth.router)
app.include_router(clients.router)


@app.get("/healthz")
def health():
    return {"status": "ok"}
