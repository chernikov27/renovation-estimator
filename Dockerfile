# syntax=docker/dockerfile:1

# --- Stage 1: build the React SPA ---
FROM node:20-slim AS frontend
WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# --- Stage 2: Python runtime that serves API + built SPA ---
FROM python:3.12-slim AS runtime
WORKDIR /app
ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml ./
COPY backend ./backend
COPY data ./data
# Editable install keeps the package at /app so config.ROOT_DIR resolves to /app
# (where data/ and frontend/dist live), not site-packages.
RUN pip install -e .

# Built static assets from stage 1 (served by FastAPI, see backend/app/main.py)
COPY --from=frontend /frontend/dist ./frontend/dist

EXPOSE 8000
# Railway injects $PORT; fall back to 8000 for local `docker run`.
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
