# NexusPortal Docker image

FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_RUN_HOST=0.0.0.0

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends openssl && \
    rm -rf /var/lib/apt/lists/*

COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .
COPY docker/docker-entrypoint.sh /docker-entrypoint.sh

RUN chmod +x /docker-entrypoint.sh && \
    mkdir -p /app/database && \
    addgroup --system nexus && \
    adduser --system --ingroup nexus nexus && \
    chown -R nexus:nexus /app /docker-entrypoint.sh

USER nexus

EXPOSE 5000

ENTRYPOINT ["/docker-entrypoint.sh"]
