#!/usr/bin/env bash
set -euo pipefail

# Smart dev script: starts mongo via docker, runs backend + frontend locally
cd "$(dirname "$0")/.."

echo "Starting MongoDB..."
docker compose up mongo -d 2>/dev/null || echo "MongoDB already running or docker not available"

echo "Starting backend..."
uv run uvicorn api.main:app --reload --port 8000 &
BACKEND_PID=$!

echo "Starting frontend..."
cd web
npm run dev -- --port 3000 &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" SIGINT SIGTERM

echo ""
echo "Backend:  http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo "Press Ctrl+C to stop"
echo ""

wait
