@echo off
echo ===================================================
echo   OptionSense - Starting Servers...
echo ===================================================

echo 1. Starting Backend (Port 8000)...
start "OptionSense Backend" cmd /k "cd backend && uvicorn main:app --host 0.0.0.0 --port 8000"

echo 2. Starting Frontend (Port 3000)...
start "OptionSense Frontend" cmd /k "cd frontend && python -m http.server 3000"

echo.
echo ===================================================
echo   Servers Launched! 🚀
echo.
echo   Please open this URL in Chrome/Edge:
echo   http://localhost:3000
echo ===================================================
pause
