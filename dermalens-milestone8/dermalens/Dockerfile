FROM python:3.12-slim
# Tesseract lets the Analyzer read ingredient lists from photos
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr && rm -rf /var/lib/apt/lists/*
WORKDIR /app/backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ .
ENV DERMALENS_DB=/data/dermalens.db
RUN mkdir -p /data
EXPOSE 8000
# --preload: the first-start seeding runs once, not once per worker
CMD ["sh", "-c", "gunicorn --preload -w 2 -b 0.0.0.0:${PORT:-8000} wsgi:app"]
