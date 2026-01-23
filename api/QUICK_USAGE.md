# Qwen3-VL 服务 - 快速参考

## 🎯 一句话总结
**上传图片 + 输入问题 → AI 推理 → 获得答案**

---

## ⚡ 最快开始 (3 步)

### 1️⃣ 启动服务
```bash
cd /home/adamliao/Qwen3-VL-Embedding/api
conda activate qwen3_vl_env
python -m uvicorn api.server:app --port 8000
```

### 2️⃣ 查看文档
```
http://localhost:8000/docs
```

### 3️⃣ 上传图片测试
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@/path/to/image.jpg" \
  -F "prompt=这个图片中有什么？"
```

---

## 📋 常用命令

### 健康检查
```bash
curl http://localhost:8000/health
```

### 获取模型信息
```bash
curl http://localhost:8000/info
```

### 上传 JPG 推理 ⭐
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@photo.jpg" \
  -F "prompt=这是什么？"
```

### 纯文本推理
```bash
curl -X POST http://localhost:8000/v1/text-inference \
  -H "Content-Type: application/json" \
  -d '{"prompt":"什么是AI？"}'
```

---

## 🐍 Python 快速代码

```python
import requests

# 上传图片推理
with open('photo.jpg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/v1/image-inference',
        files={'image': f},
        data={
            'prompt': '这个图片中有什么？',
            'max_new_tokens': 256
        }
    )
    print(response.json()['response'])
```

---

## 🔧 API 端点一览表

| 端点 | 方法 | 用途 |
|------|------|------|
| `/health` | GET | 检查服务 |
| `/info` | GET | 模型信息 |
| **`/v1/image-inference`** | **POST** | **📷 上传 JPG 推理** |
| `/v1/text-inference` | POST | 纯文本推理 |
| `/v1/image-inference-base64` | POST | Base64 图片 |
| `/v1/image-url-inference` | POST | 网络图片 |

---

## 📊 参数速查

```json
{
  "prompt": "问题或指令",           // 必需
  "max_new_tokens": 256,           // 可选，默认1024
  "temperature": 0.7,              // 可选，默认0.7
  "top_p": 0.8                     // 可选，默认0.8
}
```

### 参数含义
- `max_new_tokens`: 响应长度（128=短, 256=中, 512=长）
- `temperature`: 0=准确, 1=创意
- `top_p`: 多样性控制

---

## 🧪 测试文件

| 文件 | 命令 |
|------|------|
| Python 测试 | `python test_image_service.py` |
| cURL 测试 | `bash test_image_service.sh` |
| 使用示例 | `python example_usage.py` |

---

## 📝 使用示例

### 场景 1: 图片描述
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@sunset.jpg" \
  -F "prompt=用五句话描述这张照片"
```

### 场景 2: 文档识别
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@document.jpg" \
  -F "prompt=这是什么文件？提取关键信息"
```

### 场景 3: 对象计数
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@crowd.jpg" \
  -F "prompt=图片中有多少人？"
```

### 场景 4: 文字识别
```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@sign.jpg" \
  -F "prompt=识别并翻译图片中的文字"
```

---

## ⚠️ 常见问题

| 问题 | 解决方案 |
|------|---------|
| 连接失败 | 检查服务是否运行 |
| 导入错误 | 确保环境激活: `conda activate qwen3_vl_env` |
| 内存不足 | 减少 `max_new_tokens` 或使用 CPU |
| 图片错误 | 确保是 .jpg/.png 格式 |

---

## 📁 重要文件

| 文件 | 用途 |
|------|------|
| `IMAGE_INFERENCE_GUIDE.md` | 详细使用指南 |
| `SERVICE_SUMMARY.md` | 完整总结 |
| `api/server.py` | 服务代码 |
| `test_image_service.py` | 测试脚本 |
| `example_usage.py` | 代码示例 |

---

## 🚀 快捷键

```bash
# 启动服务
alias qwen_start="cd ~/Qwen3-VL-Embedding/api && conda activate qwen3_vl_env && python -m uvicorn api.server:app --port 8000"

# 运行测试
alias qwen_test="cd ~/Qwen3-VL-Embedding/api && conda activate qwen3_vl_env && python test_image_service.py"

# 查看文档
alias qwen_docs="open http://localhost:8000/docs"
```

---

## 💡 Pro 提示

1. **批量处理**: 在循环中使用 requests 处理多张图片
2. **超时设置**: 大图片设置 `timeout=120`
3. **错误处理**: 总是检查 response 的 status 字段
4. **性能优化**: 压缩图片以加快处理速度

---

## 🎓 学习资源

- 📖 [IMAGE_INFERENCE_GUIDE.md](IMAGE_INFERENCE_GUIDE.md) - 完整指南
- 🔗 [FastAPI 文档](https://fastapi.tiangolo.com)
- 🤖 [Qwen3-VL 官方](https://huggingface.co/Qwen/Qwen3-VL-Embedding-8B)

---

**需要帮助？** 查看 `IMAGE_INFERENCE_GUIDE.md` 的故障排除部分！

**想要深入？** 查看 `SERVICE_SUMMARY.md` 获取完整说明！

---

*最后更新: 2024 年*
