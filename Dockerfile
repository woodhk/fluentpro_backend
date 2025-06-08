# Use Python 3.11 slim image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies including curl for health checks
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements files
COPY requirements/ requirements/

# Install Python dependencies (development by default, can be overridden)
ARG REQUIREMENTS_FILE=requirements/development.txt
RUN pip install --no-cache-dir -r ${REQUIREMENTS_FILE}

# Copy project
COPY . .

# Create directory for Celery beat schedule
RUN mkdir -p /app/celerybeat

# Collect static files (if needed)
RUN python manage.py collectstatic --noinput || true

# Expose ports for Django (8000), Flower (5555)
EXPOSE 8000 5555

# Default command (can be overridden in docker-compose)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]