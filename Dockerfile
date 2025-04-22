# Use an official Python image (Debian-based)
FROM python:3.12

# Install system dependencies for eSpeak and ODBC (for pyodbc)
RUN apt-get update && apt-get install -y \
    espeak-ng libespeak-ng1 \
    gcc g++ gnupg curl apt-transport-https \
    unixodbc unixodbc-dev libpq-dev

# Set the working directory inside the container
WORKDIR /app

# Copy project files into the container
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Run the app with uvicorn instead of python
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
