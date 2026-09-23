# Stage 1: build the React/Vite frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build


# Stage 2: install runtime dependencies and serve the app via FastAPI
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libhdf5-dev \
        libnetcdf-dev \
        libeccodes-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY ml ./ml
COPY configs ./configs
COPY data ./data
COPY models ./models
COPY scripts ./scripts
COPY .env.example /app/.env.example
COPY --from=frontend-builder /frontend/dist /app/frontend_dist

RUN mkdir -p \
    /app/data/raw \
    /app/data/interim \
    /app/data/processed \
    /app/data/synthetic \
    /app/models/checkpoints \
    /app/models/metadata

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]