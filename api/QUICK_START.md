# Qwen3-VL 推理服务 - 快速开始

## 🚀 5 分钟快速上手

### 1️⃣ 安装依赖 (30 秒)

```bash
cd /home/adamliao/Qwen3-VL-Embedding/api
pip install -r requirements.txt
```

### 2️⃣ 启动服务 (2 分钟)

```bash
./start_service.sh
```

**注意**: 首次启动会自动下载模型（~15GB），请耐心等待。

### 3️⃣ 验证服务 (10 秒)

```bash
# 新开一个终端
curl http://localhost:8000/health
```

看到 `{"status": "ok"}` 表示服务正常！

### 4️⃣ 测试推理 (1 分钟)

#### 文本推理

```bash
curl -X POST http://localhost:8000/v1/text-inference \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "什么是人工智能？",
    "max_new_tokens": 200
  }'
```

#### 图片推理

```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@/path/to/your/image.jpg" \
  -F "prompt=描述这张图片"
```

### 5️⃣ 运行完整测试 (1 分钟)

```bash
python test_service.py
```

---

## 📝 Python 快速示例

```python
import requests

# 文本推理
response = requests.post(
    "http://localhost:8000/v1/text-inference",
    json={"prompt": "解释量子计算", "max_new_tokens": 200}
)
print(response.json()['response'])

# 图片推理
with open("image.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/v1/image-inference",
        files={"image": f},
        data={"prompt": "这张图片里有什么？"}
    )
print(response.json()['response'])
```

---

## ⚠️ 重要提示

### 模型要求

**本服务需要生成模型，不能使用嵌入模型！**

- ✅ **正确**: `Qwen/Qwen2-VL-7B-Instruct` (服务默认)
- ❌ **错误**: `Qwen3-VL-Embedding-8B`

### 硬件要求

- **GPU**: 推荐 16GB+ 显存 (如 V100, A100, RTX 4090)
- **内存**: 32GB+ RAM
- **存储**: 50GB+ 可用空间

### 如果使用本地模型

```bash
export QWEN_MODEL_PATH="/path/to/Qwen2-VL-7B-Instruct"
./start_service.sh
```

---

## 🔧 故障排查

### 服务无法启动？

```bash
# 检查依赖
pip install -r requirements.txt

# 检查端口
lsof -i :8000

# 查看日志
tail -f server.log
```

### 显存不足？

```python
# 在 server.py 中修改
torch_dtype="float16"  # 使用 float16
# 或
device="cpu"  # 使用 CPU（会很慢）
```

### 模型下载慢？

```bash
# 使用镜像
export HF_ENDPOINT=https://hf-mirror.com
./start_service.sh
```

---

## 📚 更多信息

- **完整文档**: 查看 `DEPLOYMENT_GUIDE.md`
- **API 文档**: http://localhost:8000/docs
- **修改记录**: 查看 `CHANGES_SUMMARY.md`
- **示例代码**: `example_usage.py`

---

## 🎯 API 端点速查

| 端点 | 方法 | 功能 |
|------|------|------|
| `/health` | GET | 健康检查 |
| `/info` | GET | 模型信息 |
| `/v1/text-inference` | POST | 纯文本推理 |
| `/v1/image-inference` | POST | 图片+文本推理 |
| `/v1/image-inference-base64` | POST | Base64 图片推理 |
| `/v1/image-url-inference` | POST | URL 图片推理 |

---

## 📞 需要帮助？

1. 查看 `DEPLOYMENT_GUIDE.md` 的故障排除部分
2. 运行 `python test_service.py` 进行诊断
3. 检查服务日志: `tail -f server.log`
4. 访问 API 文档: http://localhost:8000/docs

---

**就这么简单！祝使用愉快！** 🎉
