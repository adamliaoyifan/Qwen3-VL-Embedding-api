#!/bin/bash
# Start both Ollama agent (qwen3:14b) and Qwen3-VL service on a single GPU
#
# Expected VRAM on RTX 5090 (32GB):
#   Ollama qwen3:14b  (Q4_K_M):  ~9GB
#   Qwen3-VL-8B       (8-bit):   ~10GB
#   Overhead + KV cache:          ~2-3GB
#   Total:                        ~21GB  (11GB headroom)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# Must run VL service with cwd=$SCRIPT_DIR (quant/api/), not parent quant/,
# so `python -m api.server` resolves the nested package at quant/api/api/.

echo "========================================"
echo "Starting All Services (Single GPU)"
echo "========================================"
echo ""

# --- 1. Start Ollama agent ---
echo "[1/2] Setting up Ollama qwen3:14b agent..."
bash "$SCRIPT_DIR/setup_ollama_agent.sh"
echo ""

# --- 2. Start VL service ---
echo "[2/2] Starting Qwen3-VL-8B service (8-bit quantized)..."
echo ""

export QWEN_MODEL_PATH="${QWEN_MODEL_PATH:-/home/ubuntu/Workspace/Qwen3/models/Qwen3-VL-8B-Instruct}"
export QWEN_QUANTIZATION="${QWEN_QUANTIZATION:-8bit}"

cd "$SCRIPT_DIR"
bash "$SCRIPT_DIR/start_vl_service_quantized.sh"
