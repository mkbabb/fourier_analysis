#!/usr/bin/env bash
# Start API + frontend dev servers, auto-finding free ports.
set -euo pipefail
cd "$(dirname "$0")"

find_free_port() {
    local port=${1:-8000}
    while lsof -iTCP:"$port" -sTCP:LISTEN -t &>/dev/null; do
        ((port++))
    done
    echo "$port"
}

API_PORT=$(find_free_port 8000)
WEB_PORT=$(find_free_port 3000)

echo "Starting API  → http://localhost:$API_PORT"
echo "Starting Web  → http://localhost:$WEB_PORT"
echo ""

trap 'kill 0' EXIT

(cd web && VITE_PROXY_API="http://localhost:$API_PORT" npx vite --port "$WEB_PORT") &

uv run uvicorn api.main:app --host 0.0.0.0 --port "$API_PORT" --reload &

wait
