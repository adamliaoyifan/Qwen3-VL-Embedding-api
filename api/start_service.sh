#!/bin/bash

# Qwen3-VL 推理服务启动脚本

set -e

echo "========================================"
echo "Qwen3-VL 推理服务启动脚本"
echo "========================================"
echo ""

# 自动探测本地模型路径（优先使用用户已设置的环境变量）
if [ -z "$QWEN_MODEL_PATH" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
    DEFAULT_MODEL_PATH="$PROJECT_ROOT/models/Qwen3-VL-8B-Instruct"
    if [ -d "$DEFAULT_MODEL_PATH" ]; then
        export QWEN_MODEL_PATH="$DEFAULT_MODEL_PATH"
    fi
fi
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

# 设置API密钥 (推荐)
echo ""
echo "[2/4] 配置API密钥..."
if [ -z "$API_KEY" ]; then
    echo "⚠ 警告: API_KEY 未设置，服务将不受保护！"
    echo ""
    echo "建议设置API密钥以保护服务:"
    echo "  export API_KEY=\"adamliaoyifan\""
    echo ""
    read -p "是否现在设置API密钥? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -sp "请输入API密钥: " api_key_input
        echo
        export API_KEY="$api_key_input"
        echo "✓ API密钥已设置"
    else
        echo "⚠ 继续启动未受保护的服务..."
    fi
else
    echo "✓ API密钥已配置"
fi

# 设置模型路径 (可选)
echo ""
echo "[3/4] 配置模型..."
if [ -z "$QWEN_MODEL_PATH" ]; then
    echo "使用默认模型: Qwen/Qwen3-VL-8B-Instruct (将自动从 HuggingFace 下载)"
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
echo "[4/4] 启动服务..."
echo "服务地址: http://0.0.0.0:8000"
echo "API文档: http://localhost:8000/docs"
if [ -n "$API_KEY" ]; then
    echo "API密钥: 已启用 (从环境变量读取)"
    echo ""
    echo "使用API密钥调用服务:"
    echo "  curl 'http://localhost:8000/v1/text-inference?api_key=$API_KEY' ..."
else
    echo "API密钥: 未设置 (服务未受保护)"
fi
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动服务
#cd api
python -m api.server
