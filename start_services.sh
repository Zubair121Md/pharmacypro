#!/bin/bash

echo "🚀 Starting Pharmacy Revenue Management System..."

# Kill any existing processes
echo "🔄 Stopping existing processes..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
sleep 2

# Start Backend
echo "🐍 Starting Backend (Python/FastAPI)..."
cd /Users/zubairishaq/Desktop/clean/backend
source ../backend/venv311/bin/activate 2>/dev/null || true
nohup python3 -m uvicorn app.main_complete:app --host 127.0.0.1 --port 8000 --reload > uvicorn.log 2>&1 &
echo $! > uvicorn.pid
echo "✅ Backend started with PID: $(cat uvicorn.pid)"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/docs >/dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
done

# Start Frontend
echo "⚛️  Starting Frontend (React)..."
cd /Users/zubairishaq/Desktop/clean/frontend
nohup npm start > npm.log 2>&1 &
echo $! > npm.pid
echo "✅ Frontend started with PID: $(cat npm.pid)"

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ Frontend is ready!"
        break
    fi
    sleep 1
done

echo ""
echo "🎉 System is ready!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://127.0.0.1:8000"
echo "📚 API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "🔑 Login Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "To stop services, run: ./stop_services.sh"


echo "🚀 Starting Pharmacy Revenue Management System..."

# Kill any existing processes
echo "🔄 Stopping existing processes..."
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true
sleep 2

# Start Backend
echo "🐍 Starting Backend (Python/FastAPI)..."
cd /Users/zubairishaq/Desktop/clean/backend
source ../backend/venv311/bin/activate 2>/dev/null || true
nohup python3 -m uvicorn app.main_complete:app --host 127.0.0.1 --port 8000 --reload > uvicorn.log 2>&1 &
echo $! > uvicorn.pid
echo "✅ Backend started with PID: $(cat uvicorn.pid)"

# Wait for backend to be ready
echo "⏳ Waiting for backend to be ready..."
for i in {1..30}; do
    if curl -s http://127.0.0.1:8000/docs >/dev/null 2>&1; then
        echo "✅ Backend is ready!"
        break
    fi
    sleep 1
done

# Start Frontend
echo "⚛️  Starting Frontend (React)..."
cd /Users/zubairishaq/Desktop/clean/frontend
nohup npm start > npm.log 2>&1 &
echo $! > npm.pid
echo "✅ Frontend started with PID: $(cat npm.pid)"

# Wait for frontend to be ready
echo "⏳ Waiting for frontend to be ready..."
for i in {1..60}; do
    if curl -s http://localhost:3000 >/dev/null 2>&1; then
        echo "✅ Frontend is ready!"
        break
    fi
    sleep 1
done

echo ""
echo "🎉 System is ready!"
echo "📱 Frontend: http://localhost:3000"
echo "🔧 Backend API: http://127.0.0.1:8000"
echo "📚 API Docs: http://127.0.0.1:8000/docs"
echo ""
echo "🔑 Login Credentials:"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo "To stop services, run: ./stop_services.sh"
