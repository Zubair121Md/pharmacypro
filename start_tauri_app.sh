#!/bin/bash
# Complete startup script for Tauri Pharmacy Revenue Management System

echo "🏥 Starting Pharmacy Revenue Management System (Tauri)"
echo "====================================================="

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to kill existing processes
kill_existing() {
    echo "🔄 Stopping existing processes..."
    
    # Kill existing backend
    pkill -f "uvicorn app.main_complete:app" 2>/dev/null || true
    
    # Kill existing frontend
    pkill -f "react-scripts start" 2>/dev/null || true
    
    # Kill existing Tauri
    pkill -f "pharmacy-revenue-tauri" 2>/dev/null || true
    
    sleep 2
}

# Function to start backend
start_backend() {
    echo "📡 Starting backend server..."
    cd backend
    
    # Check if Python is available
    if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
        echo "❌ Python not found. Please install Python 3.8+"
        exit 1
    fi
    
    # Use python3 if available, otherwise python
    PYTHON_CMD=""
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    else
        PYTHON_CMD="python"
    fi
    
    # Install dependencies if needed
    echo "📦 Installing backend dependencies..."
    $PYTHON_CMD -m pip install uvicorn fastapi python-multipart pandas openpyxl scikit-learn redis aiofiles >/dev/null 2>&1
    
    # Start backend
    echo "🚀 Starting backend on port 8000..."
    $PYTHON_CMD -m uvicorn app.main_complete:app --host 127.0.0.1 --port 8000 --reload &
    BACKEND_PID=$!
    echo "Backend started with PID: $BACKEND_PID"
    cd ..
}

# Function to start frontend
start_frontend() {
    echo "🎨 Starting frontend server..."
    cd frontend
    
    # Check if Node.js is available
    if ! command -v node &> /dev/null; then
        echo "❌ Node.js not found. Please install Node.js 16+"
        exit 1
    fi
    
    # Install dependencies if needed
    if [ ! -d "node_modules" ]; then
        echo "📦 Installing frontend dependencies..."
        npm install >/dev/null 2>&1
    fi
    
    # Start frontend
    echo "🚀 Starting frontend on port 3000..."
    npm start &
    FRONTEND_PID=$!
    echo "Frontend started with PID: $FRONTEND_PID"
    cd ..
}

# Function to wait for services
wait_for_services() {
    echo "⏳ Waiting for services to be ready..."
    local max_attempts=30
    local attempts=0
    
    while [ $attempts -lt $max_attempts ]; do
        if check_port 8000 && check_port 3000; then
            echo "✅ Both services are ready!"
            return 0
        fi
        
        echo "⏳ Waiting... (attempt $((attempts + 1))/$max_attempts)"
        sleep 2
        attempts=$((attempts + 1))
    done
    
    echo "❌ Services failed to start within 60 seconds"
    return 1
}

# Function to start Tauri app
start_tauri() {
    echo "🖥️  Starting Tauri desktop app..."
    cd src-tauri
    
    # Check if Rust is available
    if ! command -v cargo &> /dev/null; then
        echo "❌ Rust/Cargo not found. Please install Rust"
        exit 1
    fi
    
    # Build and run Tauri app
    echo "🔨 Building Tauri app..."
    npm run tauri:dev &
    TAURI_PID=$!
    echo "Tauri app started with PID: $TAURI_PID"
    cd ..
}

# Main execution
main() {
    # Kill existing processes
    kill_existing
    
    # Start backend
    start_backend
    
    # Wait for backend to start
    sleep 5
    
    # Start frontend
    start_frontend
    
    # Wait for both services
    if wait_for_services; then
        echo ""
        echo "🎉 Pharmacy Revenue Management System is ready!"
        echo "📱 Backend: http://127.0.0.1:8000"
        echo "🎨 Frontend: http://127.0.0.1:3000"
        echo ""
        
        # Start Tauri app
        start_tauri
        
        echo "🖥️  Desktop app should open automatically"
        echo ""
        echo "Press Ctrl+C to stop all services"
        
        # Keep script running
        wait
    else
        echo "❌ Failed to start services. Please check the logs above."
        exit 1
    fi
}

# Run main function
main
