FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY src/ingestion/f1-api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ingestion/f1-api/f1_api_ingestion.py .

RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

ENV START_SEASON=2014 \
    END_SEASON=2025 \
    DATA_DIR=/app/data

VOLUME ["/app/data"]

CMD ["python", "f1_api_ingestion.py"]