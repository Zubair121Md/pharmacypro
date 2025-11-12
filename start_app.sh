#!/bin/bash
# Startup script for Pharmacy Revenue Management System

echo "🏥 Starting Pharmacy Revenue Management System..."

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null ; then
        return 0
    else
        return 1
    fi
}

# Function to start backend
start_backend() {
    echo "📡 Starting backend server..."
    cd backend
    if [ ! -f "app/main_complete.py" ]; then
        echo "❌ Backend files not found. Please make sure you're in the correct directory."
        exit 1
    fi
    
    # Install dependencies if needed
    if [ ! -d "venv" ]; then
        echo "📦 Creating virtual environment..."
        python3 -m venv venv
    fi
    
    source venv/bin/activate
    pip install -r requirements.txt
    
    # Start backend
    python -m uvicorn app.main_complete:app --host 127.0.0.1 --port 8000 --reload &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting frontend server..."
    cd frontend
    if [ ! -f "package.json" ]; then
        echo "❌ Frontend files not found. Please make sure you're in the correct directory."
        exit 1
    fi
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install
    fi
    
    # Start frontend
    npm start &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID"
    cd ..
}

# Function to start Tauri app
start_tauri() {
    echo "🖥️  Starting Tauri desktop app..."
    cd src-tauri
    npm run tauri:dev &
    TAURI_PID=$!
    echo "Tauri app started with PID: $TAURI_PID"
    cd ..
}

# Check if backend is already running
if check_port 8000; then
    echo "✅ Backend already running on port 8000"
else
    start_backend
    sleep 5  # Give backend time to start
fi

# Check if frontend is already running
if check_port 3000; then
    echo "✅ Frontend already running on port 3000"
else
    start_frontend
    sleep 10  # Give frontend time to start
fi

# Wait a bit for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 5

# Start Tauri app
start_tauri

echo "🎉 Pharmacy Revenue Management System started!"
echo "📱 Backend: http://127.0.0.1:8000"
echo "🎨 Frontend: http://127.0.0.1:3000"
echo "🖥️  Desktop App: Should open automatically"

# Keep script running
wait
