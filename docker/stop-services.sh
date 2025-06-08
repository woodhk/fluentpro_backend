#!/bin/bash
# Helper script to stop all services

set -e

echo "🛑 Stopping FluentPro Celery Services..."

# Navigate to docker directory
cd "$(dirname "$0")"

# Stop and remove containers
echo "📦 Stopping containers..."
docker-compose down

# Optional: Remove volumes (uncomment if you want to clear Redis data)
# echo "🗑️  Removing volumes..."
# docker-compose down -v

echo ""
echo "✅ All services stopped successfully!"
echo ""
echo "📋 To restart services:"
echo "   ./start-services.sh"
echo ""