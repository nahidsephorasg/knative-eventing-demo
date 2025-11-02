FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN groupadd --gid 1001 appgroup && \
    useradd --uid 1001 --gid 1001 --shell /bin/bash --create-home appuser

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Change ownership
RUN chown -R appuser:appgroup /app

# Switch to non-root user
USER 1001

# Default port
ENV PORT=8080
EXPOSE ${PORT}

# ========================================
# SERVICE-SPECIFIC STAGES
# ========================================

# Event Producer
FROM base AS event-producer
COPY --chown=appuser:appgroup services/event_producer/app.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]

# Data Extractor
FROM base AS data-extractor
COPY --chown=appuser:appgroup services/data_extractor/app.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]

# Content Validator
FROM base AS content-validator
COPY --chown=appuser:appgroup services/content_validator/app.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]

# Database Enricher
FROM base AS database-enricher
COPY --chown=appuser:appgroup services/database_enricher/app.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]

# Message Router
FROM base AS message-router
COPY --chown=appuser:appgroup services/message_router/app.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]

# Finance Handler
FROM base AS finance-handler
COPY --chown=appuser:appgroup services/finance_handler/app.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--worker-class", "gevent", "--workers", "1", "--timeout", "0", "app:app"]

# Support Handler
FROM base AS support-handler
COPY --chown=appuser:appgroup services/support_handler/app.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "app:app"]

# Event Monitor
FROM base AS event-monitor
COPY --chown=appuser:appgroup services/event_monitor/app.py .
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--worker-class", "gevent", "--workers", "1", "--timeout", "0", "app:app"]

# ========================================
# DATABASE IMAGE
# ========================================
FROM postgres:16 AS customer-database
COPY database/schema.sql /docker-entrypoint-initdb.d/01-schema.sql
COPY database/sample_data.sql /docker-entrypoint-initdb.d/02-data.sql
ENV POSTGRES_DB=customers
ENV POSTGRES_USER=demo
ENV POSTGRES_PASSWORD=demo123
