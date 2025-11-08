#!/bin/bash

# Peerly - Reset Qdrant Script
# Completely removes all Qdrant vector data and collections
# Use this when you want to re-embed documents from scratch

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}==================================================${NC}"
echo -e "${YELLOW}  Peerly - Reset Qdrant Vector Database${NC}"
echo -e "${YELLOW}==================================================${NC}\n"

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
    echo -e "${RED}Error: Docker Compose not found${NC}"
    echo -e "${YELLOW}Install from: https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

# Warning message
echo -e "${RED}WARNING: This will delete ALL vector embeddings and collections!${NC}"
echo -e "${YELLOW}You will need to re-run the embedding script after this.${NC}\n"

# Confirmation
read -p "Are you sure you want to proceed? (yes/no): " -r
echo
if [[ ! $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    echo -e "${BLUE}Reset cancelled${NC}"
    exit 0
fi

# Step 1: Stop Qdrant container
echo -e "${YELLOW}[1/3] Stopping Qdrant container...${NC}"
$COMPOSE_CMD stop qdrant 2>/dev/null || true
echo -e "${GREEN}✓ Qdrant stopped${NC}"

# Step 2: Remove Qdrant container and volumes
echo -e "\n${YELLOW}[2/3] Removing Qdrant container and volumes...${NC}"
$COMPOSE_CMD rm -f -v qdrant 2>/dev/null || true
echo -e "${GREEN}✓ Container removed${NC}"

# Step 3: Delete persistent data directory
echo -e "\n${YELLOW}[3/3] Deleting persistent data...${NC}"
if [ -d "data/qdrant" ]; then
    rm -rf data/qdrant/*
    echo -e "${GREEN}✓ Data directory cleared${NC}"
else
    echo -e "${BLUE}Data directory does not exist (nothing to delete)${NC}"
fi

# Also clear embedding cache if requested
echo -e "\n${YELLOW}Do you also want to clear the embedding cache?${NC}"
echo -e "${BLUE}(This will force re-generation of all embeddings via OpenAI API)${NC}"
read -p "Clear embedding cache? (yes/no): " -r
echo
if [[ $REPLY =~ ^[Yy][Ee][Ss]$ ]]; then
    if [ -d "app/embedding_cache" ]; then
        rm -rf app/embedding_cache/*
        echo -e "${GREEN}✓ Embedding cache cleared${NC}"
    else
        echo -e "${BLUE}Embedding cache directory does not exist${NC}"
    fi
else
    echo -e "${BLUE}Embedding cache preserved${NC}"
fi

echo -e "\n${GREEN}==================================================${NC}"
echo -e "${GREEN}  Qdrant Reset Complete!${NC}"
echo -e "${GREEN}==================================================${NC}\n"

echo -e "${YELLOW}Next steps:${NC}"
echo -e "1. Start Qdrant:        ${BLUE}./start.sh${NC} or ${BLUE}$COMPOSE_CMD up -d qdrant${NC}"
echo -e "2. Re-embed documents:  ${BLUE}python scripts/embed_documents.py --all${NC}"
echo -e "3. Verify collections:  ${BLUE}curl http://localhost:6333/collections${NC}\n"
