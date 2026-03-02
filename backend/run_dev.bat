@echo off
REM AI-PECO Backend Startup Script for Windows

setlocal enabledelayedexpansion

echo.
echo ===============================================
echo   AI-PECO Backend Startup
echo ===============================================
echo.

REM Check if .env exists
if not exist ".env" (
    echo ERROR: .env file not found!
    echo.
    echo Please create .env file from .env.example:
    echo   copy .env.example .env
    echo.
    echo Then edit .env and fill in:
    echo   - MONGODB_URL (from MongoDB Atlas)
    echo   - SECRET_KEY (generate: python -c "import secrets; print(secrets.token_urlsafe(32))")
    echo.
    pause
    exit /b 1
)

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if !errorlevel! neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate venv
echo Activating virtual environment...
call venv\Scripts\activate.bat
if !errorlevel! neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt -q
if !errorlevel! neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Test imports
echo.
echo Testing imports...
python test_imports.py
if !errorlevel! neq 0 (
    echo ERROR: Import test failed
    pause
    exit /b 1
)

echo.
echo ✅ All checks passed!
echo.
echo Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo API docs (Swagger): http://localhost:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

pause
