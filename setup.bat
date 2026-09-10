@echo off
echo ============================================
echo  Multi-Job Portal Automation Platform
echo  Local Setup Script
echo ============================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

REM Check Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Node.js is not installed or not in PATH.
    echo Download from: https://nodejs.org/
    pause
    exit /b 1
)

echo [1/4] Setting up Backend...
cd backend

REM Create virtual environment
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing Python dependencies...
pip install -r requirements.txt -q

REM Create .env if not exists
if not exist ".env" (
    echo Creating .env file...
    copy .env.example .env
)

REM Create uploads directory
if not exist "uploads\resumes" (
    mkdir uploads\resumes
)

cd ..

echo.
echo [2/4] Setting up Frontend...
cd frontend

REM Install dependencies
echo Installing Node.js dependencies...
call npm install

cd ..

echo.
echo [3/4] Setup complete!
echo.
echo ============================================
echo  To start the application:
echo ============================================
echo.
echo  Option 1 (Recommended): Run start.bat
echo  Option 2: Manual start (see below)
echo.
echo  Manual Start:
echo    Terminal 1 (Backend):
echo      cd backend
echo      venv\Scripts\activate
echo      uvicorn app.main:app --reload --port 8000
echo.
echo    Terminal 2 (Frontend):
echo      cd frontend
echo      npm run dev
echo.
echo  Access:
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/api/v1/docs
echo ============================================
echo.
pause
