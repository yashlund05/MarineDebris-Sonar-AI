@echo off
setlocal enabledelayedexpansion

title MarineDebris-Sonar-AI Launcher
color 0B

echo ==============================================================================
echo         MARINE DEBRIS SONAR AI -- AUTOMATED SYSTEM LAUNCHER
echo                 SIH 2026 -- Problem Statement PS26057
echo ==============================================================================
echo.

cd /d "%~dp0"

:: -----------------------------------------------------------------------------
:: Step 1: Detect Python
:: -----------------------------------------------------------------------------
echo [*] Checking Python environment...
set "SYS_PYTHON="

python --version >nul 2>&1
if %ERRORLEVEL% equ 0 (
    set "SYS_PYTHON=python"
) else (
    py --version >nul 2>&1
    if %ERRORLEVEL% equ 0 (
        set "SYS_PYTHON=py"
    )
)

if "%SYS_PYTHON%"=="" (
    if exist ".venv\Scripts\python.exe" (
        set "SYS_PYTHON=.venv\Scripts\python.exe"
    ) else (
        color 0C
        echo [ERROR] Python was not found in your system PATH!
        echo Please install Python 3.10+ from https://www.python.org/downloads/
        echo Make sure to check Add Python to PATH during installation.
        pause
        exit /b 1
    )
)

for /f "tokens=*" %%v in ('%SYS_PYTHON% --version 2^>^&1') do echo     Found Python: %%v

:: -----------------------------------------------------------------------------
:: Step 2: Detect Node.js and NPM
:: -----------------------------------------------------------------------------
echo [*] Checking Node.js environment...
node --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    color 0C
    echo [ERROR] Node.js was not found in your system PATH!
    echo Please install Node.js LTS from https://nodejs.org/
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('node --version 2^>^&1') do echo     Found Node:   %%v
for /f "tokens=*" %%v in ('call npm --version 2^>^&1') do echo     Found NPM:    v%%v

:: -----------------------------------------------------------------------------
:: Step 3: Setup Configuration File
:: -----------------------------------------------------------------------------
echo [*] Checking configuration file...
if not exist ".env" (
    if exist ".env.example" (
        echo     Creating .env from template...
        copy /y ".env.example" ".env" >nul
    ) else (
        echo     Creating default .env...
        echo ENVIRONMENT=development> .env
        echo DEBUG=false>> .env
        echo API_CORS_ORIGINS=http://localhost:2671>> .env
    )
)
echo     Configuration file is ready.

:: -----------------------------------------------------------------------------
:: Step 4: Python Dependencies and Virtualenv Resolution
:: -----------------------------------------------------------------------------
echo [*] Checking Python dependencies...
set "RUN_PYTHON="

if exist ".venv\Scripts\python.exe" (
    set "RUN_PYTHON=.venv\Scripts\python.exe"
    echo     Using existing virtual environment in .venv.
) else (
    %SYS_PYTHON% -c "import fastapi, uvicorn" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "RUN_PYTHON=%SYS_PYTHON%"
        echo     Using system Python with installed dependencies.
    ) else (
        echo     Creating local Python virtual environment in .venv...
        %SYS_PYTHON% -m venv .venv
        if !ERRORLEVEL! neq 0 (
            color 0C
            echo [ERROR] Failed to create virtual environment!
            pause
            exit /b 1
        )
        set "RUN_PYTHON=.venv\Scripts\python.exe"
        echo     Installing backend requirements into .venv...
        .venv\Scripts\python.exe -m pip install --upgrade pip
        .venv\Scripts\python.exe -m pip install -r backend\requirements.txt
        if !ERRORLEVEL! neq 0 (
            color 0C
            echo [ERROR] Failed to install backend dependencies!
            pause
            exit /b 1
        )
    )
)

:: -----------------------------------------------------------------------------
:: Step 5: Verify and Install Frontend Dependencies
:: -----------------------------------------------------------------------------
echo [*] Checking frontend dependencies...
if not exist "frontend\node_modules\" (
    echo     Installing frontend node packages...
    echo     This may take a minute on first run...
    cd frontend
    call npm install
    if !ERRORLEVEL! neq 0 (
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
:: Step 6: Create Required Data Directories
:: -----------------------------------------------------------------------------
if not exist "data\storage" mkdir "data\storage"
if not exist "models\detection" mkdir "models\detection"

:: -----------------------------------------------------------------------------
:: Step 7: Launch Backend and Frontend Services
:: -----------------------------------------------------------------------------
echo.
echo ==============================================================================
echo [*] Launching Services on Configured Ports:
echo     - Backend API:   http://localhost:5039
echo     - API Docs:      http://localhost:5039/docs
echo     - Frontend App:  http://localhost:2671
echo ==============================================================================
echo.

:: Launch Backend on Port 5039 in a new window
start "MarineDebris-Sonar-AI Backend" /d "%~dp0" cmd /k "%RUN_PYTHON% -m uvicorn backend.api.main:app --host 0.0.0.0 --port 5039 --reload"

:: Launch Frontend on Port 2671 in a new window
start "MarineDebris-Sonar-AI Frontend" /d "%~dp0frontend" cmd /k "call npm run dev"

:: Wait for services to be actively listening
echo [*] Waiting for Frontend web server to become ready on http://localhost:2671...
"%RUN_PYTHON%" "%~dp0scripts\wait_for_server.py" http://localhost:2671 25

:: Launch default web browser to the Frontend UI
echo [*] Opening application in browser: http://localhost:2671
start http://localhost:2671

echo.
echo ==============================================================================
echo [SUCCESS] MarineDebris-Sonar-AI is up and running!
echo.
echo   Web Application: http://localhost:2671
echo   Backend API:     http://localhost:5039
echo   Swagger UI:      http://localhost:5039/docs
echo.
echo   Keep the two service terminal windows open while using the application.
echo   To stop the application, simply close the two service terminal windows.
echo ==============================================================================
echo.
pause
