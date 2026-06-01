#!/bin/bash
# 
# Qwen3-VL 图片推理服务 - cURL测试命令
# 使用这些命令来测试API服务
#

API_URL="http://localhost:8000"
IMAGE_PATH="/home/adamliao/Desktop/近照.jpg"
API_KEY="adamliaoyifan"  # 从环境变量获取API密钥，如果没有则为空

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
if [ -n "$API_KEY" ]; then
  echo "命令: curl -X POST \"$API_URL/v1/text-inference?api_key=$API_KEY\""
  API_KEY_PARAM="?api_key=$API_KEY"
else
  echo "命令: curl -X POST $API_URL/v1/text-inference"
  echo "⚠ 警告: API_KEY未设置，如果服务需要API密钥，此请求将失败"
  API_KEY_PARAM=""
fi
echo -e "\n响应:"
curl -X POST "$API_URL/v1/text-inference$API_KEY_PARAM" \
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
  if [ -n "$API_KEY" ]; then
    echo "命令: curl -X POST \"$API_URL/v1/image-inference?api_key=$API_KEY" -F \"image=@$IMAGE_PATH\" ..."
    API_KEY_PARAM="?api_key=$API_KEY"
  else
    echo "命令: curl -X POST $API_URL/v1/image-inference -F \"image=@$IMAGE_PATH\" ..."
    echo "⚠ 警告: API_KEY未设置，如果服务需要API密钥，此请求将失败"
    API_KEY_PARAM=""
  fi
  echo -e "\n响应:"
  curl -X POST "$API_URL/v1/image-inference$API_KEY_PARAM" \
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
  
  if [ -n "$API_KEY" ]; then
    echo "命令: curl -X POST \"$API_URL/v1/image-inference-base64?api_key=$API_KEY""
    API_KEY_PARAM="?api_key=$API_KEY"
  else
    echo "命令: curl -X POST $API_URL/v1/image-inference-base64"
    echo "⚠ 警告: API_KEY未设置，如果服务需要API密钥，此请求将失败"
    API_KEY_PARAM=""
  fi
  echo -e "\n响应:"
  curl -X POST "$API_URL/v1/image-inference-base64$API_KEY_PARAM" \
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
