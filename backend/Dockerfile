FROM python:3.11-slim

WORKDIR /app

# Install system deps for sqlite-vec
RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all backend source
COPY . .

# Create necessary directories
RUN mkdir -p /app/dreams /app/uploads

# Initialize DB on build
RUN python database.py

# Cloud Run injects PORT env var; default to 8000 locally
ENV PORT=8080
EXPOSE 8080

CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
