#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$ROOT_DIR"

IMAGE_NAME="${IMAGE_NAME:-ai-forecast-bust-detection}"
PORT="${PORT:-8000}"
CONTAINER_NAME="${CONTAINER_NAME:-aerobust-app}"

if command -v docker >/dev/null 2>&1; then
  echo "Building Docker image: ${IMAGE_NAME}"
  docker build -t "$IMAGE_NAME" .

  echo "Stopping existing container if present: ${CONTAINER_NAME}"
  docker rm -f "$CONTAINER_NAME" >/dev/null 2>&1 || true

  echo "Starting container on port ${PORT}"
  docker run --rm -d \
    --name "$CONTAINER_NAME" \
    -p "${PORT}:8000" \
    -e PORT=8000 \
    "$IMAGE_NAME"

  echo "Application is running."
  echo "Open: http://localhost:${PORT}/"
  echo "Docs: http://localhost:${PORT}/docs"
  echo "Health: http://localhost:${PORT}/health"
  echo "To stop: docker rm -f ${CONTAINER_NAME}"
else
  echo "Docker is required but not installed or not on PATH." >&2
  exit 1
fi
