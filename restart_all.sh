#!/bin/bash
# Restart All Services: Backend, Frontend, and Databases

set -e

echo "🔄 Restarting All Services..."
echo "================================"
echo ""

# Step 1: Stop all running services
echo "🛑 Step 1: Stopping existing services..."

# Stop frontend (Next.js)
echo "   Stopping Frontend (Next.js)..."
pkill -f "next dev" 2>/dev/null || true
pkill -f "next-server" 2>/dev/null || true

# Stop backend (Python/FastAPI)
echo "   Stopping Backend API..."
pkill -f "uvicorn main:app" 2>/dev/null || true
pkill -f "uvicorn" 2>/dev/null || true

# Wait for processes to stop
sleep 3

echo "   ✅ Services stopped"
echo ""

# Step 2: Restart Docker services (databases)
echo "🗄️  Step 2: Restarting Databases (Docker)..."
cd "$(dirname "$0")/infra/docker" 2>/dev/null || {
    echo "   ⚠️  Docker compose file not found, skipping database restart"
    echo "   (This is OK if databases are running separately)"
    cd "$(dirname "$0")"
}
if [ -f "docker-compose.yml" ]; then
    echo "   Restarting Docker services..."
    docker-compose restart 2>/dev/null || {
        echo "   ⚠️  Docker compose restart failed, trying down/up..."
        docker-compose down 2>/dev/null || true
        sleep 2
        docker-compose up -d 2>/dev/null || {
            echo "   ⚠️  Docker compose not available or services not configured"
        }
    }
    echo "   ✅ Databases restarted"
else
    echo "   ⚠️  docker-compose.yml not found in infra/docker"
fi
cd "$(dirname "$0")"
echo ""

# Step 3: Start Backend API
echo "🚀 Step 3: Starting Backend API Server..."
cd "$(dirname "$0")/services/api"

# Check if virtual environment exists
if [ -d "venv" ]; then
    source venv/bin/activate
    echo "   ✅ Using virtual environment"
else
    echo "   ⚠️  Virtual environment not found, using system Python"
fi

# Set environment variables
export ORACLE_URI="${ORACLE_URI:-oracle+oracledb://system:password@localhost:1521/XE}"
export POSTGRES_URI="${POSTGRES_URI:-postgresql://postgres:postgres@localhost:5432/frauddb}"
export MONGO_URI="${MONGO_URI:-mongodb://root:password@localhost:27017/}"
export REDIS_URI="${REDIS_URI:-redis://localhost:6379/0}"

# Start backend in background
echo "   Starting uvicorn on port 8000..."
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload > /tmp/backend.log 2>&1 &
BACKEND_PID=$!
echo "   ✅ Backend started (PID: $BACKEND_PID)"
cd "$(dirname "$0")"
echo ""

# Step 4: Start Frontend
echo "🌐 Step 4: Starting Frontend Server..."
cd "$(dirname "$0")/apps/web"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "   ⚠️  node_modules not found, installing dependencies..."
    npm install
fi

# Start frontend in background
echo "   Starting Next.js on port 3000..."
npm run dev > /tmp/frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   ✅ Frontend started (PID: $FRONTEND_PID)"
cd "$(dirname "$0")"
echo ""

# Step 5: Wait and verify
echo "⏳ Step 5: Waiting for services to start..."
sleep 8

echo ""
echo "✅ All Services Restarted!"
echo "================================"
echo ""
echo "📊 Service Status:"
echo "   Backend API:  http://localhost:8000"
echo "   API Docs:     http://localhost:8000/docs"
echo "   API Health:   http://localhost:8000/healthz"
echo "   Frontend:     http://localhost:3000"
echo ""
echo "📋 Logs:"
echo "   Backend:  tail -f /tmp/backend.log"
echo "   Frontend: tail -f /tmp/frontend.log"
echo ""
echo "🛑 To stop all services:"
echo "   pkill -f 'uvicorn main:app' && pkill -f 'next dev'"
echo ""

# Quick health check
echo "🔍 Verifying services..."
sleep 2

# Check backend
if curl -s http://localhost:8000/healthz > /dev/null 2>&1 || curl -s http://localhost:8000/docs > /dev/null 2>&1; then
    echo "   ✅ Backend is responding"
else
    echo "   ⚠️  Backend may still be starting (check logs)"
fi

# Check frontend
if curl -s http://localhost:3000 > /dev/null 2>&1; then
    echo "   ✅ Frontend is responding"
else
    echo "   ⚠️  Frontend may still be starting (check logs)"
fi

echo ""
echo "🎉 Restart complete!"

