#!/bin/bash

# VPR (Visual Place Recognition) 嵌入服务启动脚本

set -e

echo "========================================"
echo "VPR 嵌入服务启动脚本"
echo "========================================"
echo ""

# 检查 Python
if ! command -v python &> /dev/null; then
    echo "错误: 未找到 Python"
    exit 1
fi

# 检查是否在正确的目录
if [ ! -f "api/api/vpr_server.py" ]; then
    echo "错误: 请在项目根目录运行此脚本"
    echo "当前目录: $(pwd)"
    exit 1
fi

# 检查依赖
echo "[1/4] 检查依赖..."
python -c "import fastapi, uvicorn, PIL, torch, torchvision, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠ 缺少依赖，正在安装..."
    pip install fastapi uvicorn pillow torch torchvision numpy
fi
echo "✓ 依赖检查完成"

# 设置API密钥 (推荐)
echo ""
echo "[2/4] 配置API密钥..."
if [ -z "$API_KEY" ]; then
    echo "⚠ 警告: API_KEY 未设置，服务将不受保护！"
    echo ""
    echo "建议设置API密钥以保护服务:"
    echo "  export API_KEY=\"your_secret_key\""
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

# 配置VPR模型
echo ""
echo "[3/4] 配置VPR模型..."

# 模型选择: eigenplaces (默认), cosplace, dinov2
VPR_MODEL="${VPR_MODEL:-eigenplaces}"
VPR_BACKBONE="${VPR_BACKBONE:-ResNet18}"
VPR_DIM="${VPR_DIM:-512}"
VPR_PORT="${VPR_PORT:-8890}"
VPR_HOST="${VPR_HOST:-0.0.0.0}"

echo "模型: $VPR_MODEL"
echo "Backbone: $VPR_BACKBONE"
echo "输出维度: $VPR_DIM"
echo ""
echo "提示: 可通过环境变量自定义配置:"
echo "  export VPR_MODEL=eigenplaces    # eigenplaces / cosplace / dinov2"
echo "  export VPR_BACKBONE=ResNet50    # ResNet18 / ResNet50 等"
echo "  export VPR_DIM=2048             # 输出维度"
echo "  export VPR_PORT=8890            # 端口"

echo ""
echo "[4/4] 启动服务..."
echo "服务地址: http://${VPR_HOST}:${VPR_PORT}"
echo "健康检查: http://localhost:${VPR_PORT}/health"
echo "嵌入接口: http://localhost:${VPR_PORT}/v1/embed"
if [ -n "$API_KEY" ]; then
    echo "API密钥: 已启用 (从环境变量读取)"
    echo ""
    echo "使用API密钥调用服务:"
    echo "  curl -X POST 'http://localhost:${VPR_PORT}/v1/embed?api_key=${API_KEY}' -F 'image=@photo.jpg'"
else
    echo "API密钥: 未设置 (服务未受保护)"
fi
echo ""
echo "按 Ctrl+C 停止服务"
echo "========================================"
echo ""

# 启动服务
python -m api.api.vpr_server --model "$VPR_MODEL" --backbone "$VPR_BACKBONE" --dim "$VPR_DIM" --port "$VPR_PORT" --host "$VPR_HOST"
