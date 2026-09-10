#!/bin/sh
set -eu

: "${DATABASE_URL:?DATABASE_URL must be configured for Vita PostgreSQL}"
npm install --include=dev
npm run db:migrate
npm run db:check
npm run build

node dist/web-api.js &
ADAPTIVE_PID=$!

cleanup() {
  kill "$ADAPTIVE_PID" 2>/dev/null || true
  wait "$ADAPTIVE_PID" 2>/dev/null || true
}
trap cleanup INT TERM EXIT

exec gunicorn app:app
