FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY src/transformation/f1_to_silver/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/transformation/f1_to_silver/f1_to_silver.py .

RUN useradd -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

ENV START_SEASON=2014 \
    END_SEASON=2025 \
    AZURE_STORAGE_ACCOUNT_URL=""

CMD ["python", "f1_to_silver.py"]