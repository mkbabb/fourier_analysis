#!/usr/bin/env bash
set -euo pipefail

DEPLOY_HOST="${DEPLOY_HOST:-mbabb.fridayinstitute.net}"
DEPLOY_PORT="${DEPLOY_PORT:-1022}"
DEPLOY_USER="${DEPLOY_USER:-mbabb}"
DEPLOY_PATH="${DEPLOY_PATH:-/var/www/fourier-analysis}"
BRANCH="${BRANCH:-master}"

echo "Deploying to ${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PORT}..."
ssh -p "${DEPLOY_PORT}" "${DEPLOY_USER}@${DEPLOY_HOST}" << ENDSSH
  set -euo pipefail
  cd "${DEPLOY_PATH}"
  git pull origin "${BRANCH}"
  docker compose -f docker-compose.yml -f docker-compose.prod.yml build
  docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d
  docker image prune -f
  docker compose ps
ENDSSH
