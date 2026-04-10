#!/bin/bash
echo "-- Starting PostgreSQL test database..."
docker-compose -f docker-compose.test.yml up -d

echo ""
echo "-- Waiting for database..."
sleep 3

echo ""
echo "-- Test database running on port 5433"
echo ""
echo "To stop: docker-compose -f docker-compose.test.yml down"