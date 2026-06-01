#!/bin/bash

# Qwen3-VL Docker Deployment Script
# This script builds and deploys the service in Docker

set -e

echo "========================================"
echo "Qwen3-VL Docker Deployment"
echo "========================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
IMAGE_NAME="qwen3-vl-inference"
CONTAINER_NAME="qwen3-vl-service"
PORT=${PORT:-8000}
MODEL_PATH=${QWEN_MODEL_PATH:-"Qwen/Qwen2-VL-7B-Instruct"}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if nvidia-docker is available (optional)
if command -v nvidia-smi &> /dev/null; then
    GPU_AVAILABLE=true
    echo -e "${GREEN}✓ GPU detected${NC}"
else
    GPU_AVAILABLE=false
    echo -e "${YELLOW}⚠ No GPU detected, will use CPU (slow)${NC}"
fi

# Navigate to project root
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

echo ""
echo "[1/5] Building Docker image..."
echo "Image: $IMAGE_NAME:latest"
echo ""

if docker build -t "$IMAGE_NAME:latest" -f api/Dockerfile .; then
    echo -e "${GREEN}✓ Image built successfully${NC}"
else
    echo -e "${RED}✗ Image build failed${NC}"
    exit 1
fi

echo ""
echo "[2/5] Stopping existing container (if any)..."
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    docker stop "$CONTAINER_NAME" || true
    docker rm "$CONTAINER_NAME" || true
    echo -e "${GREEN}✓ Old container removed${NC}"
else
    echo "No existing container found"
fi

echo ""
echo "[3/5] Starting new container..."
echo "Container name: $CONTAINER_NAME"
echo "Port mapping: $PORT:8000"
echo "Model path: $MODEL_PATH"
echo ""

# Build docker run command
DOCKER_RUN_CMD="docker run -d \
  --name $CONTAINER_NAME \
  -p $PORT:8000 \
  -v $(pwd)/api/models:/app/models \
  -e QWEN_MODEL_PATH=\"$MODEL_PATH\" \
  --restart unless-stopped"

# Add GPU support if available
if [ "$GPU_AVAILABLE" = true ]; then
    DOCKER_RUN_CMD="$DOCKER_RUN_CMD --gpus all"
fi

# Add HuggingFace mirror if set
if [ -n "$HF_ENDPOINT" ]; then
    DOCKER_RUN_CMD="$DOCKER_RUN_CMD -e HF_ENDPOINT=\"$HF_ENDPOINT\""
fi

DOCKER_RUN_CMD="$DOCKER_RUN_CMD $IMAGE_NAME:latest"

if eval "$DOCKER_RUN_CMD"; then
    echo -e "${GREEN}✓ Container started${NC}"
else
    echo -e "${RED}✗ Container start failed${NC}"
    exit 1
fi

echo ""
echo "[4/5] Waiting for service to initialize..."
echo "This may take a few minutes on first run (model download)..."
echo ""

# Wait for service to be ready
MAX_WAIT=300  # 5 minutes
WAIT_TIME=0
INTERVAL=5

while [ $WAIT_TIME -lt $MAX_WAIT ]; do
    if curl -s http://localhost:$PORT/health > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Service is ready!${NC}"
        break
    fi
    
    echo -n "."
    sleep $INTERVAL
    WAIT_TIME=$((WAIT_TIME + INTERVAL))
done

if [ $WAIT_TIME -ge $MAX_WAIT ]; then
    echo ""
    echo -e "${YELLOW}⚠ Service did not become ready in time${NC}"
    echo "Check logs: docker logs $CONTAINER_NAME"
else
    echo ""
    echo "[5/5] Verifying service..."
    
    # Get server IP
    if command -v hostname &> /dev/null; then
        SERVER_IP=$(hostname -I | awk '{print $1}')
    else
        SERVER_IP="localhost"
    fi
    
    # Health check
    if curl -s http://localhost:$PORT/health | grep -q "ok"; then
        echo -e "${GREEN}✓ Health check passed${NC}"
    else
        echo -e "${YELLOW}⚠ Health check failed${NC}"
    fi
    
    # Model info
    echo ""
    echo "Service Information:"
    echo "  - Local: http://localhost:$PORT"
    echo "  - Network: http://$SERVER_IP:$PORT"
    echo "  - API Docs: http://localhost:$PORT/docs"
    echo ""
    echo -e "${GREEN}========================================"
    echo "Deployment Complete!"
    echo "========================================${NC}"
    echo ""
    echo "Useful commands:"
    echo "  View logs:    docker logs -f $CONTAINER_NAME"
    echo "  Stop service: docker stop $CONTAINER_NAME"
    echo "  Start service: docker start $CONTAINER_NAME"
    echo "  Remove:      docker rm -f $CONTAINER_NAME"
    echo ""
    echo "Test the service:"
    echo "  curl http://localhost:$PORT/health"
    echo "  curl http://localhost:$PORT/info"
    echo ""
fi
