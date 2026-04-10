#!/bin/bash

echo "========================================"
echo "  Travel Planner - Test Runner"
echo "========================================"
echo ""

# Checks if Docker is running
echo "🔍 Checking if Docker is running..."
if ! docker ps > /dev/null 2>&1; then
    echo ""
    echo "-- ERROR: Docker is not running!"
    echo ""
    echo "Please start Docker Desktop and try again."
    echo ""
    exit 1
fi
echo "-- Docker is running"
echo ""

echo "-- Starting PostgreSQL test database..."
docker-compose -f docker-compose.test.yml up -d

if [ $? -ne 0 ]; then
    echo ""
    echo "-- ERROR: Failed to start database"
    exit 1
fi

echo ""
echo "-- Waiting for database to be ready..."
sleep 8

echo ""
echo "-- Checking database health..."
docker-compose -f docker-compose.test.yml ps

echo ""
echo "-- Running tests..."
echo ""

# Activates virtual env
source venv/bin/activate

# Tests execution
pytest -v

TEST_EXIT_CODE=$?

echo ""
echo "-- Stopping test database..."
docker-compose -f docker-compose.test.yml down

echo ""
echo "========================================"
if [ $TEST_EXIT_CODE -eq 0 ]; then
    echo "  -- All tests passed!"
else
    echo "  -- Some tests failed"
fi
echo "========================================"

exit $TEST_EXIT_CODE