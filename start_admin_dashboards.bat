@echo off
echo =========================================
echo  🚀 CRM Admin Dashboard - Quick Start
echo =========================================
echo.
echo Starting FastAPI Server...
echo.

cd /d "%~dp0"

start "CRM Backend Server" cmd /k "C:/Users/rohit/Projects/crm_backend_fastapi/.venv/Scripts/python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo Waiting for server to initialize...
timeout /t 5 /nobreak >nul

echo.
echo Opening Admin Dashboards...
echo.

echo 📊 Simple Admin Dashboard (All Tables + Terminal):
start http://127.0.0.1:8000/admin/dashboard

echo 🔧 Advanced Admin Dashboard (Full Featured):
start http://127.0.0.1:8000/admin/

echo 📖 API Documentation:
start http://127.0.0.1:8000/docs

echo.
echo =========================================
echo  ✅ Admin Dashboards Launched!
echo =========================================
echo.
echo Available URLs:
echo • Simple Dashboard: http://127.0.0.1:8000/admin/dashboard
echo • Full Dashboard:   http://127.0.0.1:8000/admin/
echo • API Docs:         http://127.0.0.1:8000/docs
echo.
echo Admin Login:
echo • Email: admin@crm.com
echo • Password: admin123
echo.
echo Press any key to exit...
pause >nul