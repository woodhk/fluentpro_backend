#!/usr/bin/env bash
echo "Starting FluentPro Backend..."
uvicorn src.main:app --host 0.0.0.0 --port $PORT