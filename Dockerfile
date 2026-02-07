# ---- Backend Dockerfile ----
FROM python:3.11-slim

# Install system dependencies for PyMuPDF and Tesseract OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install Python dependencies first (caching layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app/ ./app/
COPY .env .env

# Expose port
EXPOSE 8001

# Start the server
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]