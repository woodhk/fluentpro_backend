# Use Python 3.11 slim image
FROM python:3.11-slim

# Set build arguments
ARG REQUIREMENTS_FILE=requirements/production.txt
ARG BUILD_ENV=production

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=utf-8
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Set work directory
WORKDIR /app

# Create app user for security
RUN groupadd -r app && useradd -r -g app app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    # Build dependencies
    gcc \
    libpq-dev \
    # Runtime dependencies
    curl \
    wget \
    netcat-traditional \
    # Security updates
    && apt-get upgrade -y \
    # Cleanup
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* /var/tmp/*

# Upgrade pip and install wheel for better package installation
RUN pip install --no-cache-dir --upgrade pip wheel

# Copy requirements files first for better Docker layer caching
COPY requirements/ requirements/

# Install Python dependencies
RUN pip install --no-cache-dir -r ${REQUIREMENTS_FILE} \
    && pip install --no-cache-dir gunicorn \
    && find /usr/local -depth \( \
        \( -type d -a \( -name test -o -name tests -o -name idle_test \) \) \
        -o \( -type f -a \( -name '*.pyc' -o -name '*.pyo' \) \) \
    \) -exec rm -rf '{}' +

# Copy project files
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/staticfiles /app/mediafiles /app/logs /app/celerybeat \
    && chown -R app:app /app

# Switch to app user for security
USER app

# Collect static files (production only)
RUN if [ "$BUILD_ENV" = "production" ]; then \
        DJANGO_SETTINGS_MODULE=config.settings.production \
        SKIP_SETTINGS_VALIDATION=True \
        SECRET_KEY=build-time-secret \
        python manage.py collectstatic --noinput --clear; \
    fi

# Add health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health/ || exit 1

# Expose port
EXPOSE 8000

# Add entrypoint script for initialization
COPY docker/entrypoint.sh /entrypoint.sh
USER root
RUN chmod +x /entrypoint.sh
USER app

# Default command (production-ready with Gunicorn)
CMD ["/entrypoint.sh"]