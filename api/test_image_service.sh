#!/bin/bash
# 
# Qwen3-VL 图片推理服务 - cURL测试命令
# 使用这些命令来测试API服务
#

API_URL="http://localhost:8000"
IMAGE_PATH="/home/adamliao/Desktop/近照.jpg"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║          Qwen3-VL 图片推理服务 - cURL测试命令            ║"
echo "╚════════════════════════════════════════════════════════════╝"

# ============================================================
# 1. 健康检查
# ============================================================
echo -e "\n【测试 1】健康检查"
echo "命令: curl -X GET $API_URL/health"
echo -e "\n响应:"
curl -X GET "$API_URL/health" \
  -H "Content-Type: application/json" \
  -s | jq .

# ============================================================
# 2. 获取模型信息
# ============================================================
echo -e "\n【测试 2】获取模型信息"
echo "命令: curl -X GET $API_URL/info"
echo -e "\n响应:"
curl -X GET "$API_URL/info" \
  -H "Content-Type: application/json" \
  -s | jq .

# ============================================================
# 3. 纯文本推理
# ============================================================
echo -e "\n【测试 3】纯文本推理"
echo "命令: curl -X POST $API_URL/v1/text-inference"
echo -e "\n响应:"
curl -X POST "$API_URL/v1/text-inference" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "请用一句话总结一下机器学习的定义。",
    "max_new_tokens": 128,
    "temperature": 0.7,
    "top_p": 0.8
  }' \
  -s | jq .

# ============================================================
# 4. 图片文件推理 (需要图片存在)
# ============================================================
if [ -f "$IMAGE_PATH" ]; then
  echo -e "\n【测试 4】图片文件推理"
  echo "命令: curl -X POST $API_URL/v1/image-inference -F \"image=@$IMAGE_PATH\" ..."
  echo -e "\n响应:"
  curl -X POST "$API_URL/v1/image-inference" \
    -F "image=@$IMAGE_PATH" \
    -F "prompt=这个图片中有什么？" \
    -F "max_new_tokens=256" \
    -F "temperature=0.7" \
    -F "top_p=0.8" \
    -s | jq .
else
  echo -e "\n⚠ 【测试 4】图片文件推理 - 图片文件不存在: $IMAGE_PATH"
fi

# ============================================================
# 5. Base64编码图片推理
# ============================================================
if [ -f "$IMAGE_PATH" ]; then
  echo -e "\n【测试 5】Base64编码图片推理"
  
  # 将图片转换为Base64
  IMAGE_BASE64=$(base64 -w 0 "$IMAGE_PATH")
  
  echo "命令: curl -X POST $API_URL/v1/image-inference-base64"
  echo -e "\n响应:"
  curl -X POST "$API_URL/v1/image-inference-base64" \
    -H "Content-Type: application/json" \
    -d "{
      \"image_base64\": \"$IMAGE_BASE64\",
      \"prompt\": \"这个图片展示了什么？\",
      \"max_new_tokens\": 256,
      \"temperature\": 0.7,
      \"top_p\": 0.8
    }" \
    -s | jq .
else
  echo -e "\n⚠ 【测试 5】Base64编码图片推理 - 图片文件不存在: $IMAGE_PATH"
fi

echo -e "\n════════════════════════════════════════════════════════════"
echo "✓ 测试命令完成"
echo "════════════════════════════════════════════════════════════"
