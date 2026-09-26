#!/bin/sh
set -eu
: "${PORT:?Render must supply PORT}"
: "${HOST:?Set HOST in the Render environment}"
: "${APP_ORIGIN:?Set the public application origin}"
: "${CORS_ORIGINS:?Set allowed origins}"
: "${OPENROUTER_API_KEY:?Set the server-side service key}"
exec uvicorn server:app --host "$HOST" --port "$PORT"