# syntax=docker/dockerfile:1
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System deps for libs that may need it
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libssl-dev \
    libffi-dev \
    curl \
    ffmpeg \
    pkg-config \
    libavformat-dev \
    libavcodec-dev \
    libavdevice-dev \
    libavutil-dev \
    libswscale-dev \
    libavfilter-dev \
    libswresample-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY app.py ./
COPY *.py ./
COPY modules ./modules
COPY static ./static
COPY templates ./templates
COPY ml_models ./ml_models
COPY instance ./instance
COPY avatar ./avatar
COPY documentation ./documentation

EXPOSE 5000

# Run app
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]