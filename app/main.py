import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .db import engine, Base
from .routers import clients, auth, admin, commissions, admin_simple


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Create database tables (only for local development)
    if os.getenv("VERCEL") != "1":  # Don't create tables on Vercel
        Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: Add any cleanup here if needed


class CustomCORSMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, PATCH, OPTIONS, HEAD"
            response.headers["Access-Control-Allow-Headers"] = "Accept, Accept-Language, Content-Language, Content-Type, Authorization, X-Requested-With, Origin"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            return response
        
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        response.headers["Access-Control-Expose-Headers"] = "*"
        return response


app = FastAPI(title="SaaS Admin Dashboard - Backend", lifespan=lifespan)

# Define allowed origins
ALLOWED_ORIGINS = [
    "https://saa-s-admin-dashboard-main.vercel.app",
    "http://localhost:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3000",
    "*"  # Allow all for development - remove this in production
]

# Add custom CORS middleware first
app.add_middleware(CustomCORSMiddleware)

# Add standard CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers"
    ],
    expose_headers=["*"]
)


# Manual OPTIONS handler for preflight requests
@app.options("/{path:path}")
async def options_handler(path: str):
    return {}


app.include_router(auth.router)
app.include_router(clients.router)
app.include_router(commissions.router)
app.include_router(admin.router)
app.include_router(admin_simple.router)


@app.get("/healthz")
def health():
    return {"status": "ok"}
