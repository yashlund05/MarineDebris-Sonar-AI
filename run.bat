@echo off
setlocal enabledelayedexpansion

title MarineDebris-Sonar-AI — System Launcher
color 0B

echo ==============================================================================
echo         MARINE DEBRIS SONAR AI — AUTOMATED SYSTEM LAUNCHER
echo                 SIH 2026 — Problem Statement PS26057
echo ==============================================================================
echo.

cd /d "%~dp0"

:: -----------------------------------------------------------------------------
:: Step 1: Detect Python Installation
:: -----------------------------------------------------------------------------
echo [*] Checking Python environment...
set "PY_CMD="

python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
) else (
    py --version >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "PY_CMD=py"
    )
)

if "%PY_CMD%"=="" (
    color 0C
    echo [ERROR] Python was not found in your system PATH!
    echo Please install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('%PY_CMD% --version 2^>^&1') do echo     Found: %%v

:: -----------------------------------------------------------------------------
:: Step 2: Detect Node.js and NPM
:: -----------------------------------------------------------------------------
echo [*] Checking Node.js environment...
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] Node.js was not found in your system PATH!
    echo Please install Node.js (LTS v18 or v20+) from https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo     Found Node: %%v
for /f "tokens=*" %%v in ('npm --version 2^>^&1') do echo     Found NPM:  v%%v

:: -----------------------------------------------------------------------------
:: Step 3: Setup Configuration File (.env)
:: -----------------------------------------------------------------------------
echo [*] Checking configuration (.env)...
if not exist ".env" (
    if exist ".env.example" (
        echo     Creating .env with zero-config SQLite defaults...
        copy /y ".env.example" ".env" >nul
    ) else (
        echo     Creating default .env...
        echo ENVIRONMENT=development> .env
        echo DEBUG=false>> .env
        echo API_CORS_ORIGINS=http://localhost:2671>> .env
        echo DATABASE_URL=sqlite+aiosqlite:///./data/marine_debris_sonar.db>> .env
    )
)
echo     Configuration file ready.

:: -----------------------------------------------------------------------------
:: Step 4: Setup Python Virtual Environment
:: -----------------------------------------------------------------------------
echo [*] Checking Python virtual environment (.venv)...
if not exist ".venv\Scripts\python.exe" (
    echo     Creating Python virtual environment in .venv...
    %PY_CMD% -m venv .venv
    if %ERRORLEVEL% neq 0 (
        color 0C
        echo [ERROR] Failed to create virtual environment!
        pause
        exit /b 1
    )
    echo     Virtual environment created successfully.
)

set "VENV_PYTHON=.venv\Scripts\python.exe"
set "VENV_PIP=.venv\Scripts\pip.exe"

:: -----------------------------------------------------------------------------
:: Step 5: Verify & Install Python Dependencies
:: -----------------------------------------------------------------------------
echo [*] Checking backend dependencies...
"%VENV_PYTHON%" -c "import fastapi, uvicorn" >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo     Installing required Python packages from backend\requirements.txt...
    echo     This may take a few minutes on first run...
    "%VENV_PIP%" install --upgrade pip
    "%VENV_PIP%" install -r backend\requirements.txt
    if %ERRORLEVEL% neq 0 (
        color 0C
        echo [ERROR] Failed to install backend dependencies!
        pause
        exit /b 1
    )
) else (
    echo     Backend dependencies are already installed.
)

:: -----------------------------------------------------------------------------
:: Step 6: Verify & Install Frontend Dependencies
:: -----------------------------------------------------------------------------
echo [*] Checking frontend dependencies...
if not exist "frontend\node_modules\" (
    echo     Installing frontend node packages (npm install)...
    echo     This may take a few minutes on first run...
    cd frontend
    call npm install
    if %ERRORLEVEL% neq 0 (
        color 0C
        echo [ERROR] Failed to install frontend packages!
        cd ..
        pause
        exit /b 1
    )
    cd ..
) else (
    echo     Frontend packages are already installed.
)

:: -----------------------------------------------------------------------------
:: Step 7: Create Required Data Directories
:: -----------------------------------------------------------------------------
if not exist "data\storage" mkdir "data\storage"
if not exist "models\detection" mkdir "models\detection"

:: -----------------------------------------------------------------------------
:: Step 8: Launch Backend & Frontend Services
:: -----------------------------------------------------------------------------
echo.
echo ==============================================================================
echo [*] Launching Services on Specified Ports:
echo     - Backend API:   http://localhost:5039
echo     - API Docs:      http://localhost:5039/docs
echo     - Frontend App:  http://localhost:2671
echo ==============================================================================
echo.

:: Launch Backend in separate window with port 5039
start "MarineDebris-Sonar-AI Backend [Port 5039]" cmd /k "cd /d "%~dp0" && title Backend (Port 5039) && color 0A && echo ============================================== && echo   FastAPI Backend Server - http://localhost:5039 && echo ============================================== && .venv\Scripts\python.exe -m uvicorn backend.api.main:app --host 0.0.0.0 --port 5039 --reload"

:: Launch Frontend in separate window with port 2671
start "MarineDebris-Sonar-AI Frontend [Port 2671]" cmd /k "cd /d "%~dp0\frontend" && title Frontend (Port 2671) && color 09 && echo ============================================== && echo   Vite React Frontend - http://localhost:2671 && echo ============================================== && npm run dev -- --port 2671 --host"

:: Wait for services to bind ports
echo Waiting 4 seconds for servers to initialize...
timeout /t 4 /nobreak >nul

:: Launch default web browser to frontend
echo [*] Opening application in default browser...
start http://localhost:2671

echo.
echo ==============================================================================
echo [SUCCESS] MarineDebris-Sonar-AI is running!
echo.
echo   Frontend UI:  http://localhost:2671
echo   Backend API:  http://localhost:5039
echo   Swagger UI:   http://localhost:5039/docs
echo.
echo   Keep both terminal windows open while using the application.
echo   To stop the application, simply close both terminal windows.
echo ==============================================================================
echo.
pause
