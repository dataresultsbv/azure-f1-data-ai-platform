FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install certs and map the RedHat symlink that DuckDB expects by default
RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    && mkdir -p /etc/pki/tls/certs \
    && ln -s /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt \
    && rm -rf /var/lib/apt/lists/*

COPY src/aggregation/f1_to_gold/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/aggregation/f1_to_gold/f1_to_gold.py .

RUN useradd -m -u 8888 appuser && chown -R appuser:appuser /app
USER appuser

CMD ["python", "f1_to_gold.py"]