#!/bin/bash
# Helper script to start all services with Docker Compose

set -e

echo "🚀 Starting FluentPro Celery Services..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Navigate to docker directory
cd "$(dirname "$0")"

# Pull latest images
echo "📦 Pulling latest images..."
docker-compose pull

# Build services
echo "🔨 Building services..."
docker-compose build

# Start services
echo "🎯 Starting services..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service status
echo "📊 Service Status:"
docker-compose ps

# Display access information
echo ""
echo "✅ Services started successfully!"
echo ""
echo "🌐 Access URLs:"
echo "   • Flower Dashboard: http://localhost:5555"
echo "   • Redis: localhost:6379"
echo ""
echo "🔐 Flower Login:"
echo "   • Username: admin"
echo "   • Password: dev123"
echo ""
echo "📋 Useful Commands:"
echo "   • View logs: docker-compose logs -f [service_name]"
echo "   • Stop services: docker-compose down"
echo "   • Restart service: docker-compose restart [service_name]"
echo ""
echo "🔍 Monitor with:"
echo "   • Flower: http://localhost:5555"
echo "   • Docker logs: docker-compose logs -f"
echo ""