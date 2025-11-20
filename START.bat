@echo off
echo ==========================================
echo Starting AI Senior Living Placement Assistant
echo ==========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Check if .env file exists
if not exist ".env" (
    echo .env file not found!
    echo Copying .env.example to .env...
    copy .env.example .env
    echo Please edit .env and add your GEMINI_API_KEY
    echo.
)

REM Check if dependencies are installed
python -c "import flask" 2>nul
if errorlevel 1 (
    echo Installing Python dependencies...
    pip install -r requirements.txt
)

REM Start backend server
echo Starting backend server (port 5050)...
start "Backend Server" cmd /k "venv\Scripts\activate.bat && python app.py"

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Check if frontend dependencies are installed
if not exist ".studio_import\node_modules" (
    echo Installing frontend dependencies...
    cd .studio_import
    call npm install
    cd ..
)

REM Start frontend server
echo Starting frontend server (port 3000)...
cd .studio_import
start "Frontend Server" cmd /k "npm run dev"
cd ..

echo.
echo ==========================================
echo Servers started successfully!
echo ==========================================
echo.
echo Frontend: http://localhost:3000
echo Backend:  http://localhost:5050 (internal)
echo.
echo Two windows will open - keep them both open!
echo Close both windows to stop the servers.
echo.
pause

