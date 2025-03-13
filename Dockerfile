# Use Python 3.10 slim image as base
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy other necessary files
COPY src/core/solver.py ./src/core/
COPY src/web/app.py ./src/web/
COPY src/web/templates ./src/web/templates
COPY data/word_comparison.jsonl ./data/

# Create logs directory
RUN mkdir -p logs

# Install dependencies and curl for health check
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port 8080 for Flask
EXPOSE 8080

# Set environment variables
ENV FLASK_APP=src/web/app.py
ENV FLASK_ENV=production

# Add health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/ || exit 1

# Start gunicorn with 4 worker processes
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120", "src.web.app:app"]
