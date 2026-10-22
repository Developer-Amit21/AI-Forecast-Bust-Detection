# ==========================================
# Stage 1: Build the React / Vite Frontend
# ==========================================
FROM node:20-alpine AS frontend-builder

WORKDIR /frontend

COPY frontend/package*.json ./
RUN npm ci || npm install

COPY frontend/ .
RUN npm run build

# ==========================================
# Stage 2: Python 3.11 Runtime & FastAPI
# ==========================================
FROM python:3.11-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PORT=8000

# Install NetCDF and system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libhdf5-dev \
    libnetcdf-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r requirements.txt

COPY backend ./backend
COPY data ./data
COPY generate_mock_weather_data.py ./generate_mock_weather_data.py

# Copy compiled frontend from Stage 1 into /app/frontend_dist
COPY --from=frontend-builder /frontend/dist /app/frontend_dist

EXPOSE 8000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
