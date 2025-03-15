FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including libraries needed for PDF processing and diagnostic tools
RUN apt-get update && apt-get install -y \
    libffi-dev \
    libssl-dev \
    build-essential \
    python3-dev \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    poppler-utils \
    curl \
    procps \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user to run the application
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Add additional packages for PDF and DOCX handling
RUN pip install --no-cache-dir PyPDF2==3.0.1 python-docx==0.8.11 reportlab==4.0.4 pillow==10.0.1

# Copy application code
COPY . .

# Set ownership to the non-root user
RUN chown -R appuser:appuser /app

# Set environment variables for better logging and performance
ENV PYTHONUNBUFFERED=1
ENV PORT=8000
ENV WORKERS=4
ENV TIMEOUT=120
ENV MAX_REQUESTS=1000
ENV MAX_REQUESTS_JITTER=50

# Switch to non-root user
USER appuser

# Expose port for the application
EXPOSE 8000

# Create a startup script with healthcheck
RUN echo '#!/bin/bash\n\
echo "Starting AI Resume Analyzer..."\n\
echo "Environment: $(python -V)"\n\
echo "Current directory: $(pwd)"\n\
echo "Files: $(ls -la)"\n\
\n\
# Run the application with Gunicorn for production\n\
exec gunicorn app.main:app \\\n\
    --bind 0.0.0.0:${PORT} \\\n\
    --workers ${WORKERS} \\\n\
    --timeout ${TIMEOUT} \\\n\
    --worker-class uvicorn.workers.UvicornWorker \\\n\
    --max-requests ${MAX_REQUESTS} \\\n\
    --max-requests-jitter ${MAX_REQUESTS_JITTER} \\\n\
    --access-logfile - \\\n\
    --error-logfile - \\\n\
    --log-level info\n\
' > /app/start.sh && chmod +x /app/start.sh

# Command to run the application
CMD ["/app/start.sh"]

# Add health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1