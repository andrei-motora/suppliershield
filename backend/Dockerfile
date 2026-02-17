FROM python:3.11-slim

WORKDIR /app

# Install curl for health checks
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

# Install backend + engine dependencies
COPY backend/requirements.txt backend/requirements.txt
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt -r backend/requirements.txt

# Copy engine source + data + backend
COPY src/ src/
COPY data/ data/
COPY backend/ backend/

# Set PYTHONPATH so src.* imports work without sys.path hacks
ENV PYTHONPATH=/app

# Create upload directory
RUN mkdir -p /tmp/suppliershield/sessions

# Run as non-root user
RUN adduser --disabled-password --gecos "" appuser
RUN chown -R appuser:appuser /tmp/suppliershield
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8000/api/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
