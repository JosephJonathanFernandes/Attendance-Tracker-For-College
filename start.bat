@echo off
echo Starting Attendance Tracker...

WHERE docker >nul 2>nul
IF %ERRORLEVEL% EQU 0 (
    echo Docker found! Starting with Docker Compose...
    docker compose up --build
) ELSE (
    echo Docker not found. Starting manually...
    
    echo Starting Backend...
    start cmd /k "cd attendance-tracker-backend && python -m venv venv && venv\Scripts\activate && pip install -r requirements.txt && python init_db.py && flask run"
    
    echo Starting Frontend...
    start cmd /k "cd attendance-tracker-frontend && npm install && npm run dev"
    
    echo Application starting in new windows.
)
pause
