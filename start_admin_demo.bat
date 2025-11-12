@echo off
echo Starting CRM Backend Server...
start "CRM Backend" cmd /c "cd /d C:\Users\rohit\Projects\crm_backend_fastapi && C:/Users/rohit/Projects/crm_backend_fastapi/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

echo Waiting for server to start...
timeout /t 3 /nobreak >nul

echo Testing admin endpoints...
C:/Users/rohit/Projects/crm_backend_fastapi/.venv/Scripts/python.exe test_admin.py

echo.
echo Opening admin dashboard in browser...
start http://127.0.0.1:8000/admin/

echo.
echo Opening API documentation...
start http://127.0.0.1:8000/docs

pause