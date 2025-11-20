#!/bin/bash

echo "=========================================="
echo "Starting AI Senior Living Placement Assistant"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please run: python3 -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "📦 Activating virtual environment..."
source venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found!"
    echo "Copying .env.example to .env..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your GEMINI_API_KEY"
    echo ""
fi

# Check if dependencies are installed
if ! python3 -c "import flask" 2>/dev/null; then
    echo "📥 Installing Python dependencies..."
    pip install -r requirements.txt
fi

# Start backend server
echo "🚀 Starting backend server (port 5050)..."
python3 app.py &
BACKEND_PID=$!

# Wait for backend to start
sleep 3

# Check if frontend dependencies are installed
if [ ! -d ".studio_import/node_modules" ]; then
    echo "📥 Installing frontend dependencies..."
    cd .studio_import
    npm install
    cd ..
fi

# Start frontend server
echo "🚀 Starting frontend server (port 3000)..."
cd .studio_import
npm run dev &
FRONTEND_PID=$!

echo ""
echo "=========================================="
echo "✅ Servers started successfully!"
echo "=========================================="
echo ""
echo "🌐 Frontend: http://localhost:3000"
echo "🔧 Backend:  http://localhost:5050 (internal)"
echo ""
echo "Press Ctrl+C to stop both servers"
echo ""

# Wait for user interrupt
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT TERM
wait

