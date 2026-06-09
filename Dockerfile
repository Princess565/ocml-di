# ── OCML-DI Dockerfile ──────────────────────────────────────────
# Multi-stage build for a lean production image
# Base: Python 3.11 slim (matches your .venv Python version)

FROM python:3.11-slim AS base

# System dependencies needed by opencv, pyzbar, and cryptography
RUN apt-get update && apt-get install -y --no-install-recommends \
    libzbar0 \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir "python-jose[cryptography]" "passlib[bcrypt]" bcrypt==4.0.1

# Copy the full project
COPY . .

# Create data directory if not present
RUN mkdir -p /app/data

# Expose FastAPI port
EXPOSE 8000

# Run the app
CMD ["python", "-m", "uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
