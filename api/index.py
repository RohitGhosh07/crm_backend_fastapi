"""
Vercel serverless function entry point for FastAPI application.
"""
import sys
import os

# Add the parent directory to Python path so we can import our app
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.main import app

# Vercel expects the ASGI application to be available as 'app'
# This is the entry point for Vercel serverless functions