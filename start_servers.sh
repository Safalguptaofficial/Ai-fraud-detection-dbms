#!/bin/bash
# Start Backend and Frontend Servers

set -e

echo "🛑 Stopping existing servers..."
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "next dev" 2>/dev/null || true
sleep 2

echo "📦 Setting up environment variables..."
export ORACLE_URI="${ORACLE_URI:-oracle+oracledb://system:password@localhost:1521/XE}"
export POSTGRES_URI="${POSTGRES_URI:-postgresql://postgres:postgres@localhost:5432/frauddb}"
export MONGO_URI="${MONGO_URI:-mongodb://root:password@localhost:27017/}"

echo "🚀 Starting Backend API Server..."
cd "$(dirname "$0")/services/api"
# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   Using virtual environment"
fi
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

echo "🚀 Starting Frontend Server..."
cd "$(dirname "$0")/apps/web"
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

echo ""
echo "⏳ Waiting for servers to start..."
sleep 8

echo ""
echo "✅ Servers started!"
echo "   Backend: http://localhost:8000"
echo "   Frontend: http://localhost:3000"
echo "   Health: http://localhost:8000/healthz"
echo ""
echo "📋 Logs:"
echo "   Backend: tail -f /tmp/backend.log"
echo "   Frontend: tail -f /tmp/frontend.log"
echo ""
echo "🛑 To stop: pkill -f 'uvicorn main:app' && pkill -f 'next dev'"

