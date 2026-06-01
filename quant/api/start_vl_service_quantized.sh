#!/bin/bash
# Start Qwen3-VL-8B Inference Service with 8-bit quantization
# VRAM usage: ~10GB (down from ~18GB with BF16)

set -e

echo "========================================"
echo "Qwen3-VL-8B Inference Service (8-bit)"
echo "========================================"
echo ""

# --- Model path ---
if [ -z "$QWEN_MODEL_PATH" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
    DEFAULT_MODEL_PATH="$PROJECT_ROOT/models/Qwen3-VL-8B-Instruct"
    if [ -d "$DEFAULT_MODEL_PATH" ]; then
        export QWEN_MODEL_PATH="$DEFAULT_MODEL_PATH"
    else
        # Fallback to HF model id when local model is not found
        export QWEN_MODEL_PATH="Qwen/Qwen3-VL-8B-Instruct"
    fi
fi

# --- Quantization: 8bit (recommended) or 4bit ---
#export QWEN_QUANTIZATION="${QWEN_QUANTIZATION:-4bit}"
export QWEN_QUANTIZATION="${QWEN_QUANTIZATION:-8bit}"

echo "Model:         $QWEN_MODEL_PATH"
echo "Quantization:  $QWEN_QUANTIZATION"
echo ""

echo "[1/3] Checking dependencies..."
if ! python -c "import bitsandbytes" &> /dev/null 2>&1; then
    echo "ERROR: bitsandbytes not installed."
    echo "  Run: pip install bitsandbytes"
    exit 1
fi
echo "  Dependencies OK"

# --- Evict Ollama models from VRAM to free space for VL service ---
if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
    LOADED=$(curl -sf http://localhost:11434/api/ps 2>/dev/null \
        | python3 -c "
import sys, json
data = json.load(sys.stdin)
models = [m['name'] for m in data.get('models', [])]
print('\n'.join(models))
" 2>/dev/null)
    if [ -n "$LOADED" ]; then
        echo ""
        echo "[VRAM] Evicting Ollama models from GPU memory..."
        while IFS= read -r model; do
            echo "  Unloading: $model"
            curl -sf http://localhost:11434/api/generate \
                -d "{\"model\":\"$model\",\"keep_alive\":0}" > /dev/null 2>&1 || true
        done <<< "$LOADED"
        sleep 5
        echo "  Done. Ollama server stays running on port 11434."
    fi
fi

# --- Check model exists ---
echo "[2/3] Checking model..."
if [ ! -d "$QWEN_MODEL_PATH" ]; then
    echo "ERROR: Model not found at $QWEN_MODEL_PATH"
    echo "Set QWEN_MODEL_PATH to your local model directory"
    exit 1
fi
echo "  Model found at $QWEN_MODEL_PATH"

# --- API key ---
echo "[3/3] Configuring service..."
if [ -z "$API_KEY" ]; then
    echo "  WARNING: API_KEY not set, service will be unprotected"
    echo "  Set with: export API_KEY=\"your-key\""
fi

# --- Check Ollama VRAM usage ---
if command -v nvidia-smi &> /dev/null; then
    echo ""
    echo "Current GPU VRAM usage:"
    nvidia-smi --query-gpu=memory.used,memory.total --format=csv,noheader,nounits | \
        awk -F', ' '{printf "  %dMB / %dMB (%.0f%% used, %dMB free)\n", $1, $2, $1/$2*100, $2-$1}'
fi

echo ""
echo "========================================"
echo "Starting VL service on port 8000..."
echo "  API docs:  http://localhost:8000/docs"
echo "  Health:    http://localhost:8000/health"
echo "  VRAM:      ~10GB (8-bit) / ~7GB (4-bit)"
echo "========================================"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# --- Start (cwd must be this directory so `api` resolves to ./api/, not ../api/) ---
SERVICE_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SERVICE_ROOT"
python -m api.server
