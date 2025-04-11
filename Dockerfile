# Use an official Python image (Debian-based)
FROM python:3.12-slim

# Install system dependencies (e.g. for text-to-speech like eSpeak, if needed)
RUN apt-get update && apt-get install -y \
    libpq-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /app

# Copy your project files into the container
COPY . .

# Optional: If you have a requirements.txt
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Run the app using Gunicorn with Uvicorn workers
CMD ["gunicorn", "app:app", "--workers", "4", "--worker-class", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000"]

