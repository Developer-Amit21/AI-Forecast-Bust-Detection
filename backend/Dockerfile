FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for NetCDF4 and HDF5
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libhdf5-dev \
    libnetcdf-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu -r /app/backend/requirements.txt

COPY backend /app/backend
COPY data /app/data
COPY generate_mock_weather_data.py /app/generate_mock_weather_data.py

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
