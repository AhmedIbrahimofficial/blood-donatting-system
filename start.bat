@echo off
echo Starting LifeLink Backend...
start cmd /k "cd /d d:\blood-donor-backend && venv\Scripts\uvicorn app.main:app --reload"

echo Starting LifeLink Frontend...
start cmd /k "cd /d d:\blood-donor-backend\lifeline-connect && bun run dev"

echo.
echo Both servers starting...
echo Backend:  http://localhost:8000
echo Frontend: http://localhost:8082
echo API Docs: http://localhost:8000/docs
echo.
timeout /t 3
start http://localhost:8082
