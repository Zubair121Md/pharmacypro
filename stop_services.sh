#!/bin/bash

echo "🛑 Stopping Pharmacy Revenue Management System..."

# Stop Backend
if [ -f "/Users/zubairishaq/Desktop/clean/backend/uvicorn.pid" ]; then
    BACKEND_PID=$(cat /Users/zubairishaq/Desktop/clean/backend/uvicorn.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🐍 Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm /Users/zubairishaq/Desktop/clean/backend/uvicorn.pid
        echo "✅ Backend stopped"
    else
        echo "⚠️  Backend was not running"
    fi
else
    echo "⚠️  No backend PID file found"
fi

# Stop Frontend
if [ -f "/Users/zubairishaq/Desktop/clean/frontend/npm.pid" ]; then
    FRONTEND_PID=$(cat /Users/zubairishaq/Desktop/clean/frontend/npm.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "⚛️  Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm /Users/zubairishaq/Desktop/clean/frontend/npm.pid
        echo "✅ Frontend stopped"
    else
        echo "⚠️  Frontend was not running"
    fi
else
    echo "⚠️  No frontend PID file found"
fi

# Kill any remaining processes
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true

echo "✅ All services stopped"


echo "🛑 Stopping Pharmacy Revenue Management System..."

# Stop Backend
if [ -f "/Users/zubairishaq/Desktop/clean/backend/uvicorn.pid" ]; then
    BACKEND_PID=$(cat /Users/zubairishaq/Desktop/clean/backend/uvicorn.pid)
    if kill -0 $BACKEND_PID 2>/dev/null; then
        echo "🐍 Stopping Backend (PID: $BACKEND_PID)..."
        kill $BACKEND_PID
        rm /Users/zubairishaq/Desktop/clean/backend/uvicorn.pid
        echo "✅ Backend stopped"
    else
        echo "⚠️  Backend was not running"
    fi
else
    echo "⚠️  No backend PID file found"
fi

# Stop Frontend
if [ -f "/Users/zubairishaq/Desktop/clean/frontend/npm.pid" ]; then
    FRONTEND_PID=$(cat /Users/zubairishaq/Desktop/clean/frontend/npm.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo "⚛️  Stopping Frontend (PID: $FRONTEND_PID)..."
        kill $FRONTEND_PID
        rm /Users/zubairishaq/Desktop/clean/frontend/npm.pid
        echo "✅ Frontend stopped"
    else
        echo "⚠️  Frontend was not running"
    fi
else
    echo "⚠️  No frontend PID file found"
fi

# Kill any remaining processes
pkill -f "uvicorn" 2>/dev/null || true
pkill -f "react-scripts" 2>/dev/null || true
pkill -f "npm start" 2>/dev/null || true

echo "✅ All services stopped"
