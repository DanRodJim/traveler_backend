#!/bin/bash
echo "-- Stopping PostgreSQL test database..."
docker-compose -f docker-compose.test.yml down

echo ""
echo "-- Test database stopped"