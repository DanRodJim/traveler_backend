@echo off
echo ========================================
echo   Travel Planner - Test Runner
echo ========================================
echo.

REM Checks if Docker is running
echo -- Checking if Docker is running...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo -- ERROR: Docker is not running!
    echo.
    echo -- Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo -- Docker is running
echo.

echo -- Starting PostgreSQL test database...
docker-compose -f docker-compose.test.yml up -d

if %errorlevel% neq 0 (
    echo.
    echo -- ERROR: Failed to start database
    pause
    exit /b 1
)

echo.
echo -- Waiting for database to be ready...
timeout /t 8 /nobreak > nul

echo.
echo -- Checking database health...
docker-compose -f docker-compose.test.yml ps

echo.
echo -- Running tests...
echo.

REM Activates virtual env
call venv\Scripts\activate.bat

REM Tests execution
pytest -v

set TEST_EXIT_CODE=%errorlevel%

echo.
echo -- Stopping test database...
docker-compose -f docker-compose.test.yml down

echo.
echo ========================================
if %TEST_EXIT_CODE% equ 0 (
    echo -- All tests passed!
) else (
    echo -- Some tests failed
)
echo ========================================
pause

exit /b %TEST_EXIT_CODE%