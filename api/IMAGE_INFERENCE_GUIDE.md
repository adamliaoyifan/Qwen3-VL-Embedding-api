# Qwen3-VL 图片推理服务使用指南

## 📋 服务概述

这是一个基于 **Qwen3-VL-Embedding-8B** 的AI图片理解和推理服务。服务能够：

✅ 接收用户的文本提示（prompt）  
✅ 接收并读取上传的图片文件（.jpg, .png 等）  
✅ 基于图片和提示进行智能推理  
✅ 返回详细的推理结果  

---

## 🚀 快速开始

### 1. 启动服务

在项目根目录运行：

```bash
# 激活conda环境
conda activate qwen3_vl_env

# 进入api目录
cd api

# 启动服务
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

看到以下输出表示服务启动成功：
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 2. 查看API文档

启动服务后，在浏览器打开：

- **交互式文档**：http://localhost:8000/docs
- **参考文档**：http://localhost:8000/redoc

---

## 🖼️ 使用 .jpg 文件测试服务

### 方法1：使用 Python 客户端（推荐）

```bash
# 运行测试客户端
python test_image_service.py
```

这会自动测试所有功能，包括：
- ✓ 健康检查
- ✓ 模型信息查询
- ✓ 纯文本推理
- ✓ 图片文件推理
- ✓ Base64图片推理

### 方法2：使用 cURL 命令

```bash
# 1. 健康检查
curl -X GET http://localhost:8000/health

# 2. 获取模型信息
curl -X GET http://localhost:8000/info

# 3. 上传 .jpg 文件进行推理
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@/home/adamliao/Desktop/近照.jpg" \
  -F "prompt=这个图片中有什么？" \
  -F "max_new_tokens=256" \
  -F "temperature=0.7" \
  -F "top_p=0.8"
```

### 方法3：使用 Python requests

```python
import requests

# 图片推理
with open('/home/adamliao/Desktop/近照.jpg', 'rb') as f:
    files = {'image': f}
    data = {
        'prompt': '这个图片中有什么？',
        'max_new_tokens': 256,
        'temperature': 0.7,
        'top_p': 0.8
    }
    
    response = requests.post(
        'http://localhost:8000/v1/image-inference',
        files=files,
        data=data
    )
    
    print(response.json())
```

---

## 📡 API 端点详解

### 1. 健康检查
```
GET /health
```

**响应示例：**
```json
{
  "status": "ok",
  "service": "Qwen3-VL Inference Server"
}
```

### 2. 获取模型信息
```
GET /info
```

**响应示例：**
```json
{
  "model": "Qwen3-VL-Embedding-8B",
  "status": "ready",
  "device": "cuda",
  "dtype": "torch.bfloat16"
}
```

### 3. 纯文本推理
```
POST /v1/text-inference
```

**请求体：**
```json
{
  "prompt": "请用一句话总结一下机器学习的定义。",
  "max_new_tokens": 128,
  "temperature": 0.7,
  "top_p": 0.8
}
```

**响应：**
```json
{
  "status": "success",
  "response": "机器学习是一种人工智能技术，通过让计算机从数据中学习规律和特征来改进任务性能..."
}
```

### 4. 图片文件推理 ⭐ 主要功能
```
POST /v1/image-inference
```

**请求参数（Form-data）：**
- `image` (file, 必需): 上传的图片文件（.jpg, .png 等）
- `prompt` (string, 必需): 文本提示，例如"这个图片中有什么？"
- `max_new_tokens` (integer, 可选): 最大生成 token 数，默认 1024
- `temperature` (float, 可选): 生成温度，默认 0.7
- `top_p` (float, 可选): top_p 采样参数，默认 0.8

**cURL 示例：**
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@/path/to/image.jpg" \
  -F "prompt=这个图片中有什么？请详细描述。" \
  -F "max_new_tokens=256" \
  -F "temperature=0.7" \
  -F "top_p=0.8"
```

**响应：**
```json
{
  "status": "success",
  "response": "这张图片展示了一个美丽的风景场景..."
}
```

### 5. Base64 编码图片推理
```
POST /v1/image-inference-base64
```

**请求体：**
```json
{
  "image_base64": "iVBORw0KGgoAAAANSUhEUgAAAAUA...",
  "prompt": "这个图片展示了什么？",
  "max_new_tokens": 256,
  "temperature": 0.7,
  "top_p": 0.8
}
```

### 6. 图片 URL 推理
```
POST /v1/image-url-inference
```

**请求参数（Form-data）：**
- `image_url` (string): 图片 URL
- `prompt` (string): 文本提示
- `max_new_tokens` (integer): 最大 token 数
- `temperature` (float): 生成温度
- `top_p` (float): top_p 采样参数

---

## 📝 使用场景示例

### 场景 1：图片内容理解
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@photo.jpg" \
  -F "prompt=请描述这张照片中的主要对象和背景"
```

### 场景 2：文档识别
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@document.jpg" \
  -F "prompt=这是什么类型的文档？请提取其中的关键信息"
```

### 场景 3：图片分类
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@screenshot.jpg" \
  -F "prompt=这个截图来自哪个应用程序？"
```

### 场景 4：问答
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@scene.jpg" \
  -F "prompt=图片中有几个人？他们在做什么？"
```

---

## ⚙️ 性能参数调整

| 参数 | 默认值 | 范围 | 说明 |
|------|-------|------|------|
| `max_new_tokens` | 1024 | 1-2048 | 生成文本的最大长度 |
| `temperature` | 0.7 | 0.0-1.0 | 越高越随机，越低越确定 |
| `top_p` | 0.8 | 0.0-1.0 | 核采样，控制词表多样性 |

### 推荐设置：
- **快速响应**：`max_new_tokens=128, temperature=0.5`
- **详细描述**：`max_new_tokens=512, temperature=0.7`
- **创意模式**：`max_new_tokens=1024, temperature=0.9`

---

## 🔧 故障排除

### 问题 1：无法连接到服务
```
ConnectionRefusedError: Connection refused
```

**解决方案：**
1. 确保服务已启动：`python -m uvicorn api.server:app --port 8000`
2. 检查端口是否被占用：`lsof -i :8000`
3. 尝试使用 localhost 而不是 0.0.0.0：`http://localhost:8000`

### 问题 2：模型加载失败
```
Error loading ASGI app. Could not import module "api.server"
```

**解决方案：**
1. 确保在正确的目录：`cd /home/adamliao/Qwen3-VL-Embedding/api`
2. 确保激活了正确的 conda 环境：`conda activate qwen3_vl_env`
3. 检查依赖是否安装：`pip install -r requirements-api.txt`

### 问题 3：CUDA 内存不足
```
RuntimeError: CUDA out of memory
```

**解决方案：**
1. 减少 `max_new_tokens`：`128` 或 `256`
2. 使用 CPU 推理（慢）：编辑 `api/api/inference.py`，设置 `device="cpu"`
3. 使用较小的模型

### 问题 4：图片格式不支持
```
Image format not recognized
```

**解决方案：**
- 确保上传的是标准格式：`.jpg`, `.png`, `.jpeg`
- 转换图片格式：
```bash
convert input.bmp output.jpg  # 需要 ImageMagick
```

---

## 📊 监控和日志

### 查看实时日志
启动服务时会输出详细的处理日志：
```
INFO:     Processing image inference: 这个图片中有什么？...
INFO:     Image inference completed successfully
```

### 调整日志级别
```bash
# 详细日志
python -m uvicorn api.server:app --log-level debug

# 最少日志
python -m uvicorn api.server:app --log-level warning
```

---

## 💡 最佳实践

1. **批量处理**：使用脚本处理多张图片
2. **错误处理**：总是检查响应的 `status` 字段
3. **超时设置**：对于大图片设置足够的超时时间
4. **并发限制**：不要同时发送过多请求，避免内存溢出

---

## 📚 更多资源

- [Qwen3-VL 官方文档](https://huggingface.co/Qwen/Qwen3-VL-Embedding-8B)
- [FastAPI 文档](https://fastapi.tiangolo.com/)
- [项目 README](./README.md)

---

## 🤝 反馈和支持

遇到问题？请检查：
1. 服务是否正常运行（访问 `/health` 端点）
2. 模型是否正确加载（查看服务启动日志）
3. 图片文件是否有效（检查文件大小和格式）
4. 网络连接是否正常（检查 firewall）

祝你使用愉快！ 🎉
