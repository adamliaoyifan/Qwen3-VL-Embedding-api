#!/bin/bash
# Setup and run Ollama Qwen3:14b agent service (Q4_K_M quantized by default)
# VRAM usage: ~9GB

set -e

echo "========================================"
echo "Ollama Qwen3:14b Agent Setup"
echo "========================================"

# --- helper: HTTP GET command (curl/wget) ---
HTTP_GET_CMD=""
if command -v curl &> /dev/null; then
    HTTP_GET_CMD="curl -fsSL"
elif command -v wget &> /dev/null; then
    HTTP_GET_CMD="wget -qO-"
fi

# --- 1. Install Ollama if not present ---
if ! command -v ollama &> /dev/null; then
    echo "[1/3] Installing Ollama..."
    if [ -z "$HTTP_GET_CMD" ]; then
        echo "ERROR: Neither curl nor wget is installed."
        echo "Install one of them first, then rerun this script."
        echo "Example:"
        echo "  sudo apt update && sudo apt install -y curl"
        exit 1
    fi
    INSTALL_OK=0
    for attempt in 1 2 3; do
        echo "  Install attempt ${attempt}/3..."
        if sh -c "$HTTP_GET_CMD https://ollama.com/install.sh" | sh; then
            INSTALL_OK=1
            break
        fi
        echo "  Attempt ${attempt} failed (likely network interruption)."
        sleep 3
    done

    if [ "$INSTALL_OK" -ne 1 ]; then
        echo "ERROR: Ollama installation failed after 3 attempts."
        echo "Try again with a stable network, then rerun this script."
        echo "Manual retry command:"
        echo "  curl -fsSL https://ollama.com/install.sh | sh"
        exit 1
    fi

    if ! command -v ollama &> /dev/null; then
        echo "ERROR: Install script finished but ollama command not found."
        exit 1
    fi
else
    echo "[1/3] Ollama already installed: $(ollama --version)"
fi

# --- 2. Start Ollama server ---
echo "[2/3] Starting Ollama server..."

# Configure for single-GPU coexistence with VL service
export OLLAMA_NUM_PARALLEL=1          # limit concurrent requests to save VRAM
export OLLAMA_MAX_LOADED_MODELS=1     # only keep 1 model in VRAM
export OLLAMA_HOST=0.0.0.0:11434      # listen on all interfaces

# Check if ollama is already serving
if [ -z "$HTTP_GET_CMD" ]; then
    echo "ERROR: Need curl or wget to perform health checks."
    echo "Install one of them first, then rerun this script."
    echo "Example:"
    echo "  sudo apt update && sudo apt install -y curl"
    exit 1
fi

if sh -c "$HTTP_GET_CMD http://localhost:11434/api/tags" > /dev/null 2>&1; then
    echo "  Ollama server already running"
else
    echo "  Starting ollama serve in background..."
    nohup ollama serve > /tmp/ollama.log 2>&1 &
    sleep 3
    if ! sh -c "$HTTP_GET_CMD http://localhost:11434/api/tags" > /dev/null 2>&1; then
        echo "ERROR: Ollama server failed to start. Check /tmp/ollama.log"
        exit 1
    fi
    echo "  Ollama server started (PID: $(pgrep -f 'ollama serve'))"
fi

# --- 3. Pull and verify model ---
echo "[3/3] Pulling qwen3:14b (Q4_K_M, ~9GB)..."
ollama pull qwen3:14b

echo ""
echo "========================================"
echo "Ollama Qwen3:14b Agent Ready"
echo "========================================"
echo ""
echo "Endpoints:"
echo "  API:        http://localhost:11434"
echo "  Generate:   POST http://localhost:11434/api/generate"
echo "  Chat:       POST http://localhost:11434/api/chat"
echo ""
echo "Quick test:"
echo '  curl http://localhost:11434/api/generate -d '"'"'{"model":"qwen3:14b","prompt":"Hello","stream":false}'"'"''
echo ""
echo "VRAM usage: ~9GB (Q4_K_M quantized)"
echo "Remaining for VL service: ~23GB on RTX 5090"
echo ""
echo "To stop:  pkill -f 'ollama serve'"
echo "Logs:     tail -f /tmp/ollama.log"
