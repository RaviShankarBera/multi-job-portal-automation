@echo off
echo ============================================
echo  Starting Multi-Job Portal Automation Platform
echo ============================================
echo.

REM Start Backend
echo Starting Backend (port 8000)...
start "JobPortal-Backend" cmd /k "cd backend && venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start Frontend
echo Starting Frontend (port 3000)...
start "JobPortal-Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ============================================
echo  Application Started!
echo ============================================
echo.
echo  Frontend: http://localhost:3000
echo  Backend:  http://localhost:8000
echo  API Docs: http://localhost:8000/api/v1/docs
echo.
echo  Close this window or press Ctrl+C to stop.
echo  To stop all services, close the Backend and Frontend windows.
echo ============================================
echo.
pause
