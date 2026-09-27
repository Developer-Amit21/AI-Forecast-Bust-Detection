# Stage 1: build the React/Vite frontend
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
ARG VITE_API_URL
ENV VITE_API_URL=${VITE_API_URL}
RUN npm run build


# Stage 2: install runtime dependencies and serve the app via FastAPI
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000 \
    DATA_MODE=synthetic \
    MODEL_DIR=/var/data/models/checkpoints \
    DATA_DIR=/var/data/data

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
COPY --from=frontend-builder /frontend/dist /app/frontend_dist

# Create persistent data directories
RUN mkdir -p \
    /var/data/models/checkpoints \
    /var/data/models/metadata \
    /var/data/data/raw \
    /var/data/data/interim \
    /var/data/data/processed \
    /var/data/data/synthetic

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]