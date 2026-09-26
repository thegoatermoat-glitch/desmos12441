# syntax=docker/dockerfile:1
FROM node:22-bookworm-slim AS frontend-build
WORKDIR /app/frontend
COPY frontend/ ./
RUN if [ -f yarn.lock ]; then \
      yarn install --frozen-lockfile --ignore-engines --network-timeout 120000; \
    else \
      yarn install --ignore-engines --network-timeout 120000; \
    fi
ENV REACT_APP_BACKEND_URL=/
ENV GENERATE_SOURCEMAP=false
ENV DISABLE_EMERGENT_OVERLAY=true
ENV ENABLE_HEALTH_CHECK=false
RUN yarn build

FROM python:3.11-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app/backend
COPY backend/requirements-render.txt ./requirements-render.txt
RUN pip install --no-cache-dir -r requirements-render.txt \
    && useradd --create-home --uid 10001 appuser
COPY --chown=appuser:appuser backend/ ./
COPY --from=frontend-build --chown=appuser:appuser /app/frontend/build /app/frontend/build
COPY --chown=appuser:appuser scripts/start-render.sh /app/start-render.sh
USER appuser
CMD ["sh", "/app/start-render.sh"]