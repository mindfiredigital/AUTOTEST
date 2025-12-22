FROM python:3.11-slim

WORKDIR /app

# # RUN apt-get update && apt-get install -y gcc && rm -rf /var/lib/apt/lists/*
# RUN apt-get update \
#   && apt-get install -y --no-install-recommends \
#   gcc \
#   default-libmysqlclient-dev \
#   pkg-config \
#   && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app

CMD ["python", "main.py"]