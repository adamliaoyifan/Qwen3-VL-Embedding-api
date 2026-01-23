# Qwen3-VL 图片推理服务 - 完整总结

## 📌 服务概述

已成功创建一个基于 **Qwen3-VL-Embedding-8B** 的完整图片推理服务，可以：

✅ **接收文本提示 (Prompt)** - 用户可以提交任何问题或指令  
✅ **处理上传的图片** - 支持 .jpg, .png 等多种格式  
✅ **执行推理** - 基于图片和文本联合理解，生成智能回答  
✅ **返回结果** - 以 JSON 格式返回推理结果  

---

## 🎯 核心功能

### 主要端点

| 端点 | 方法 | 功能 | 用途 |
|------|------|------|------|
| `/health` | GET | 健康检查 | 验证服务是否运行 |
| `/info` | GET | 模型信息 | 获取模型配置信息 |
| **`/v1/image-inference`** | **POST** | **📷 图片推理** | **上传 .jpg 文件进行推理** |
| `/v1/text-inference` | POST | 文本推理 | 纯文本推理 |
| `/v1/image-inference-base64` | POST | Base64 推理 | Base64 编码图片推理 |
| `/v1/image-url-inference` | POST | URL 推理 | 远程 URL 图片推理 |

---

## 🚀 快速使用指南

### 步骤 1: 启动服务

```bash
# 进入项目目录
cd /home/adamliao/Qwen3-VL-Embedding/api

# 激活环境
conda activate qwen3_vl_env

# 启动服务
python -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload
```

看到以下输出表示成功：
```
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 步骤 2: 用 .jpg 文件测试

#### 方法 A：使用 cURL（最简单）

```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@/home/adamliao/Desktop/近照.jpg" \
  -F "prompt=这个图片中有什么？" \
  -F "max_new_tokens=256"
```

#### 方法 B：使用 Python

```python
import requests

with open('/home/adamliao/Desktop/近照.jpg', 'rb') as f:
    files = {'image': f}
    data = {
        'prompt': '这个图片中有什么？请详细描述。',
        'max_new_tokens': 256,
        'temperature': 0.7,
        'top_p': 0.8
    }
    
    response = requests.post(
        'http://localhost:8000/v1/image-inference',
        files=files,
        data=data
    )
    
    print(response.json()['response'])
```

#### 方法 C：运行测试脚本

```bash
# 自动测试所有功能
python test_image_service.py

# 或运行示例脚本
python example_usage.py
```

---

## 📁 项目文件结构

```
/home/adamliao/Qwen3-VL-Embedding/api/
├── api/                          # 核心模块
│   ├── __init__.py
│   ├── server.py                 # FastAPI服务器 (306行)
│   └── inference.py              # 推理引擎 (222行)
│
├── scripts/                      # 启动脚本
│   ├── start_server.sh
│   ├── start_server_conda.sh
│   ├── start_server_prod.sh
│   └── docker_run.sh
│
├── 📝 使用文档
│   ├── IMAGE_INFERENCE_GUIDE.md  # ⭐ 图片推理完整指南
│   ├── README_API.md             # API 总体介绍
│   ├── API_QUICK_START.md        # 快速开始
│   ├── DEPLOY_GUIDE.md           # 部署指南
│   ├── SERVICE_OVERVIEW.md       # 服务概览
│   └── QUICK_REFERENCE.md        # 快速参考
│
├── 🧪 测试工具
│   ├── test_image_service.py     # ⭐ Python 测试客户端
│   ├── test_image_service.sh     # cURL 测试命令
│   └── example_usage.py          # ⭐ 使用示例代码
│
├── ⚙️ 配置文件
│   ├── requirements-api.txt      # 依赖
│   ├── Dockerfile                # Docker 配置
│   └── docker-compose.yml        # Docker Compose
│
└── 📦 其他文件
    ├── __init__.py
    ├── quick_start.py
    └── api/                       # (子模块)
```

---

## 💡 使用场景示例

### 场景 1: 图片内容分析
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@photo.jpg" \
  -F "prompt=请描述这张照片的内容和氛围"
```

### 场景 2: 文档 OCR 和理解
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@invoice.jpg" \
  -F "prompt=这是什么类型的文档？提取其中的关键信息"
```

### 场景 3: 图片分类识别
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@screenshot.jpg" \
  -F "prompt=这个截图来自哪个应用？"
```

### 场景 4: 视觉问答 (VQA)
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@scene.jpg" \
  -F "prompt=图片中有多少人？他们在做什么？"
```

---

## 📊 API 请求/响应示例

### 请求
```bash
POST /v1/image-inference
Content-Type: multipart/form-data

image: <binary file data>
prompt: "这个图片中有什么？"
max_new_tokens: 256
temperature: 0.7
top_p: 0.8
```

### 响应
```json
{
  "status": "success",
  "response": "这张图片展示了一个美丽的风景场景，包含山脉、森林和清澈的湖水。天空呈现出温暖的夕阳颜色，整体氛围宁静祥和。"
}
```

---

## ⚙️ 性能参数说明

| 参数 | 默认值 | 范围 | 说明 |
|------|-------|------|------|
| `max_new_tokens` | 1024 | 1-2048 | 生成文本的最大长度 |
| `temperature` | 0.7 | 0.0-1.0 | 越低越确定，越高越随机 |
| `top_p` | 0.8 | 0.0-1.0 | 核采样多样性控制 |

### 推荐设置

- **快速响应**：`max_new_tokens=128, temperature=0.5`
- **平衡**：`max_new_tokens=256, temperature=0.7`（推荐）
- **详细描述**：`max_new_tokens=512, temperature=0.7`
- **创意模式**：`max_new_tokens=1024, temperature=0.9`

---

## 🔍 API 交互式文档

启动服务后访问以下地址查看完整的交互式文档：

- **Swagger UI** (推荐): http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

在 Swagger UI 中可以直接测试所有 API 端点！

---

## 📦 支持的图片格式

✅ **支持的格式**：
- `.jpg` / `.jpeg`
- `.png`
- `.bmp`
- `.gif`
- `.webp`
- `.tiff`

✅ **推荐格式**：`.jpg` (兼容性最好，文件小)

---

## 🛠️ 故障排除

### 问题：无法连接到服务
```
ConnectionRefusedError: Connection refused
```

**解决方案**：
```bash
# 1. 确保激活了环境
conda activate qwen3_vl_env

# 2. 确保在正确目录
cd /home/adamliao/Qwen3-VL-Embedding/api

# 3. 重新启动服务
python -m uvicorn api.server:app --port 8000
```

### 问题：导入错误
```
Error loading ASGI app. Could not import module "api.server"
```

**解决方案**：
- 检查 `api/api/server.py` 的导入是否使用相对导入 `from .inference import`

### 问题：CUDA 内存不足
```
RuntimeError: CUDA out of memory
```

**解决方案**：
- 减少 `max_new_tokens` 值
- 使用更小的图片
- 编辑 `api/api/inference.py` 设置 `device="cpu"`（性能会降低）

---

## 📚 文件说明

### 核心文件

| 文件 | 功能 | 行数 |
|------|------|------|
| `api/server.py` | FastAPI 服务器，定义所有 API 端点 | 306 |
| `api/inference.py` | 推理引擎，处理模型加载和推理 | 222 |

### 测试和示例

| 文件 | 用途 |
|------|------|
| `test_image_service.py` | 完整的 Python 测试客户端，可测试所有功能 |
| `test_image_service.sh` | cURL 测试命令集合 |
| `example_usage.py` | 实际使用示例代码 |

### 文档

| 文件 | 内容 |
|------|------|
| `IMAGE_INFERENCE_GUIDE.md` | ⭐ 完整的图片推理使用指南 |
| `README_API.md` | API 概览和使用说明 |
| `API_QUICK_START.md` | 快速开始指南 |
| `DEPLOY_GUIDE.md` | 部署和配置指南 |

---

## ✅ 已验证的功能

✅ 服务启动和健康检查  
✅ 模型信息查询  
✅ 图片文件上传和处理  
✅ 文本提示和推理  
✅ Base64 编码图片处理  
✅ URL 图片处理  
✅ 纯文本推理  
✅ CORS 跨域请求支持  
✅ 错误处理和异常捕获  

---

## 🚀 下一步

### 推荐操作顺序

1. **启动服务** (第一个终端)
   ```bash
   cd /home/adamliao/Qwen3-VL-Embedding/api
   conda activate qwen3_vl_env
   python -m uvicorn api.server:app --port 8000
   ```

2. **查看 API 文档** (浏览器)
   ```
   http://localhost:8000/docs
   ```

3. **运行测试** (第二个终端)
   ```bash
   cd /home/adamliao/Qwen3-VL-Embedding/api
   conda activate qwen3_vl_env
   python test_image_service.py
   ```

4. **集成到你的应用**
   - 参考 `example_usage.py` 中的代码
   - 使用 `requests` 库进行 API 调用

---

## 📞 技术支持

遇到问题？检查以下事项：

1. ✓ 服务是否运行（访问 `/health`）
2. ✓ 模型是否加载（查看启动日志）
3. ✓ 图片文件是否有效（检查格式和大小）
4. ✓ 网络连接是否正常

---

## 📖 更多资源

- [Qwen3-VL HuggingFace](https://huggingface.co/Qwen/Qwen3-VL-Embedding-8B)
- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [项目代码位置](/home/adamliao/Qwen3-VL-Embedding/api)

---

**祝你使用愉快！** 🎉

如有问题，请查阅 `IMAGE_INFERENCE_GUIDE.md` 获取更详细的说明。
