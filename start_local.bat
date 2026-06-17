@echo off
echo Iniciando CarbonAudit.ai (backend + frontend)...

start "Backend (FastAPI)" cmd /k "cd /d %~dp0 && python -m uvicorn backend.main:app --reload --port 8000"
timeout /t 2 /nobreak >nul
start "Frontend (Vite)" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo Backend: http://localhost:8000
echo Frontend: http://localhost:5173
echo.
pause
