FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

COPY src/aggregation/f1_to_gold/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/aggregation/f1_to_gold/f1_to_gold.py .

RUN useradd -m -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "f1_to_gold.py"]