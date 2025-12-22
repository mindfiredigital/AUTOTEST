FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8001

# Run FastAPI application
# CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001", "--reload"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
