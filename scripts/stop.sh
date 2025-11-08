#!/bin/bash

# Peerly - Stop script
# Stops all running services

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
# Get the project root (parent of scripts directory)
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Change to project root directory
cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Stopping Peerly services...${NC}"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Determine docker-compose command (v1 vs v2)
if command_exists docker-compose; then
    COMPOSE_CMD="docker-compose"
elif command_exists docker && docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    COMPOSE_CMD=""
fi

# Stop Peerly backend
if [ -f logs/peerly-backend.pid ]; then
    PEERLY_BACKEND_PID=$(cat logs/peerly-backend.pid)
    if kill -0 $PEERLY_BACKEND_PID 2>/dev/null; then
        echo -e "${GREEN}Stopping Peerly backend (PID: $PEERLY_BACKEND_PID)...${NC}"
        kill $PEERLY_BACKEND_PID
        rm logs/peerly-backend.pid
    else
        echo -e "${YELLOW}Peerly backend process not running${NC}"
        rm logs/peerly-backend.pid
    fi
else
    echo -e "${YELLOW}No Peerly backend PID file found${NC}"
fi

# Stop frontend
if [ -f logs/frontend.pid ]; then
    FRONTEND_PID=$(cat logs/frontend.pid)
    if kill -0 $FRONTEND_PID 2>/dev/null; then
        echo -e "${GREEN}Stopping frontend (PID: $FRONTEND_PID)...${NC}"
        kill $FRONTEND_PID
        rm logs/frontend.pid
    else
        echo -e "${YELLOW}Frontend process not running${NC}"
        rm logs/frontend.pid
    fi
else
    echo -e "${YELLOW}No frontend PID file found${NC}"
fi

# Kill any remaining uvicorn or vite processes
pkill -f "uvicorn app.main:app" 2>/dev/null
pkill -f "vite" 2>/dev/null

# Stop Qdrant docker container (keeps data persistent)
if [ -n "$COMPOSE_CMD" ]; then
    echo -e "${YELLOW}Stopping Qdrant...${NC}"
    $COMPOSE_CMD stop qdrant 2>/dev/null
    echo -e "${BLUE}Note: Qdrant data is preserved in ./data/qdrant${NC}"
else
    echo -e "${YELLOW}Docker Compose not found, skipping Qdrant shutdown${NC}"
fi

echo -e "${GREEN}All services stopped${NC}"
