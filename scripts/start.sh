#!/bin/bash

# Peerly - Multi-agentic Peer Review System
# Startup script to launch both frontend and backend

set -e  # Exit on error

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

echo -e "${BLUE}==================================================${NC}"
echo -e "${BLUE}  Peerly - Technical Manuscript Review System${NC}"
echo -e "${BLUE}==================================================${NC}\n"

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found!${NC}"
    echo -e "${YELLOW}Please create a .env file based on .env.example${NC}"
    echo -e "${YELLOW}Example: cp .env.example .env${NC}"
    echo -e "${YELLOW}Then add your OPENAI_API_KEY to the .env file${NC}"
    exit 1
fi

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check for Python
if ! command_exists python3; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check for Node.js
if ! command_exists node; then
    echo -e "${RED}Error: Node.js is not installed${NC}"
    exit 1
fi

# Check for npm
if ! command_exists npm; then
    echo -e "${RED}Error: npm is not installed${NC}"
    exit 1
fi

# Check for Docker and docker-compose
if ! command_exists docker; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo -e "${YELLOW}Install from: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
    echo -e "${RED}Error: docker-compose is not installed${NC}"
    echo -e "${YELLOW}Install from: https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

# Determine docker-compose command (v1 vs v2)
if command_exists docker-compose; then
    COMPOSE_CMD="docker-compose"
else
    COMPOSE_CMD="docker compose"
fi

# Function to kill process on a specific port
kill_port() {
    local port=$1
    local pids=$(lsof -ti:$port 2>/dev/null)

    if [ -n "$pids" ]; then
        echo -e "${YELLOW}Found process(es) using port $port. Cleaning up...${NC}"
        echo "$pids" | xargs kill -9 2>/dev/null
        echo -e "${GREEN}Port $port is now free${NC}"
    fi
}

# Clean up ports before starting services
echo -e "${YELLOW}Checking for processes on ports 8000 and 5173...${NC}"
kill_port 8000  # Backend port
kill_port 5173  # Frontend port

# Start Qdrant vector database
echo -e "${GREEN}[1/4] Starting Qdrant vector database...${NC}"
$COMPOSE_CMD up -d qdrant

# Wait for Qdrant to be ready
echo -e "${YELLOW}Waiting for Qdrant to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:6333/healthz > /dev/null 2>&1; then
        echo -e "${GREEN}Qdrant is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}Qdrant failed to start. Check docker logs: $COMPOSE_CMD logs qdrant${NC}"
        exit 1
    fi
done

# Install Peerly backend dependencies
echo -e "${GREEN}[2/4] Installing Peerly backend dependencies...${NC}"
if command_exists uv; then
    echo -e "${BLUE}Using uv for faster dependency installation${NC}"
    uv sync
else
    echo -e "${YELLOW}uv not found, using pip${NC}"
    pip install -e .
fi

# Install frontend dependencies
echo -e "\n${GREEN}[3/4] Installing frontend dependencies...${NC}"
cd frontend
if [ ! -d "node_modules" ]; then
    npm install
else
    echo -e "${BLUE}Frontend dependencies already installed${NC}"
fi
cd ..

# Create log directory
mkdir -p logs

# Start Peerly backend (unified service with AI review, file management, and LaTeX compilation)
echo -e "\n${GREEN}[4/4] Starting Peerly backend server (port 8000)...${NC}"
if command_exists uv; then
    uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/peerly-backend.log 2>&1 &
else
    python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > logs/peerly-backend.log 2>&1 &
fi
PEERLY_BACKEND_PID=$!
echo -e "${BLUE}Peerly backend started with PID: $PEERLY_BACKEND_PID${NC}"

# Wait for Peerly backend to be ready
echo -e "${YELLOW}Waiting for Peerly backend to be ready...${NC}"
for i in {1..30}; do
    if curl -s http://localhost:8000/api/health > /dev/null 2>&1; then
        echo -e "${GREEN}Peerly backend is ready!${NC}"
        break
    fi
    sleep 1
    if [ $i -eq 30 ]; then
        echo -e "${RED}Peerly backend failed to start. Check logs/peerly-backend.log for details${NC}"
        kill $PEERLY_BACKEND_PID 2>/dev/null
        exit 1
    fi
done

# Start frontend
echo -e "\n${GREEN}Starting frontend server...${NC}"
cd frontend
npm run dev > ../logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${BLUE}Frontend started with PID: $FRONTEND_PID${NC}"
cd ..

# Save PIDs to file for easy cleanup
echo $PEERLY_BACKEND_PID > logs/peerly-backend.pid
echo $FRONTEND_PID > logs/frontend.pid

echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}  Peerly is now running!${NC}"
echo -e "${GREEN}==================================================${NC}"
echo -e "${BLUE}Frontend:${NC}         http://localhost:5173"
echo -e "${BLUE}Backend API:${NC}      http://localhost:8000"
echo -e "${BLUE}API Docs:${NC}         http://localhost:8000/docs"
echo -e "${BLUE}Qdrant UI:${NC}        http://localhost:6333/dashboard"
echo -e "\n${YELLOW}Services:${NC}"
echo -e "  - Qdrant Vector Database - port 6333 (persistent storage in ./data/qdrant)"
echo -e "  - Peerly Backend (AI Review, File Manager, LaTeX Compiler) - port 8000"
echo -e "  - Frontend Web App - port 5173"
echo -e "\n${YELLOW}Press Ctrl+C to stop all services${NC}"
echo -e "${YELLOW}Or run: ./scripts/stop.sh${NC}\n"

# Function to cleanup on exit
cleanup() {
    echo -e "\n${YELLOW}Shutting down services...${NC}"
    kill $PEERLY_BACKEND_PID 2>/dev/null
    kill $FRONTEND_PID 2>/dev/null
    rm -f logs/peerly-backend.pid logs/frontend.pid

    # Stop Qdrant docker container (keeps data persistent)
    echo -e "${YELLOW}Stopping Qdrant...${NC}"
    $COMPOSE_CMD stop qdrant

    echo -e "${GREEN}All services stopped${NC}"
    echo -e "${BLUE}Note: Qdrant data is preserved in ./data/qdrant${NC}"
    exit 0
}

# Trap Ctrl+C
trap cleanup INT TERM

# Wait for background processes
wait
