#!/bin/bash

# Qwen3-VL 推理服务启动脚本

set -e

echo "========================================"
echo "Qwen3-VL 推理服务启动脚本"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "api/server.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    echo "当前目录: $(pwd)"
    exit 1
fi

# 检查依赖
echo "[1/3] 检查依赖..."
python -c "import fastapi, uvicorn, PIL, torch, transformers" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ 缺少依赖，正在安装..."
    pip install fastapi uvicorn python-multipart pillow torch transformers qwen-vl-utils
fi
echo "✓ 依赖检查完成"

# 设置模型路径 (可选)
echo ""
echo "[2/3] 配置模型..."
if [ -z "$QWEN_MODEL_PATH" ]; then
    echo "使用默认模型: Qwen/Qwen2-VL-7B-Instruct (将自动从 HuggingFace 下载)"
    echo ""
    echo "如需使用本地模型，请设置环境变量:"
    echo "  export QWEN_MODEL_PATH=\"/path/to/model\""
else
    echo "使用本地模型: $QWEN_MODEL_PATH"
fi

# 设置 HuggingFace 镜像 (可选)
if [ -z "$HF_ENDPOINT" ]; then
    echo ""
    echo "提示: 如果下载慢，可以设置镜像源:"
    echo "  export HF_ENDPOINT=https://hf-mirror.com"
fi

echo ""
echo "[3/3] 启动服务..."
echo "服务地址: http://0.0.0.0:8000"
echo "API文档: http://localhost:8000/docs"
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动服务
#cd api
python -m api.server
