#!/usr/bin/env bash
# Deploy fourier-analysis to production server.
# Usage: ./deploy.sh
set -euo pipefail

REMOTE_USER="mbabb"
REMOTE_HOST="mbabb.fridayinstitute.net"
REMOTE_PORT="1022"
REMOTE_DIR="/var/www/fourier-analysis"

SSH_CMD="ssh -p ${REMOTE_PORT} ${REMOTE_USER}@${REMOTE_HOST}"

echo "==> Pushing to GitHub..."
git push origin master

echo "==> Deploying to ${REMOTE_HOST}:${REMOTE_DIR}..."
${SSH_CMD} bash -s <<'REMOTE_SCRIPT'
set -euo pipefail
cd /var/www/fourier-analysis

echo "    Pulling latest..."
git fetch origin
git reset --hard origin/master

echo "    Rebuilding containers..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml build --parallel

echo "    Restarting services..."
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

echo "    Waiting for services..."
sleep 5

echo "    Container status:"
docker compose -f docker-compose.yml -f docker-compose.prod.yml ps

echo "    Health check:"
curl -sf http://localhost:8091/api/health 2>/dev/null && echo " -> API OK" || echo " -> API endpoint not responding (may need /api/health route)"
curl -sf http://localhost:8091/ 2>/dev/null | head -c 100 && echo "" && echo " -> Frontend OK" || echo " -> Frontend check"

echo "==> Deploy complete!"
REMOTE_SCRIPT
