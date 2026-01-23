# Qwen3-VL Remote Inference Service - 部署指南

本指南详细说明如何部署和使用 Qwen3-VL 远程推理服务。

## 目录

1. [重要说明](#重要说明)
2. [系统要求](#系统要求)
3. [安装步骤](#安装步骤)
4. [启动服务](#启动服务)
5. [使用服务](#使用服务)
6. [故障排除](#故障排除)
7. [代码修复说明](#代码修复说明)

---

## 重要说明

### ⚠️ 模型选择

**关键区别**:

- **Qwen3-VL-Embedding-8B** (嵌入模型)
  - ❌ **不能**用于文本生成
  - ✅ 只能生成向量表示（embeddings）
  - 用途：检索、相似度计算、聚类等

- **Qwen2-VL-7B-Instruct** (生成模型)
  - ✅ **可以**用于文本生成
  - ✅ 支持图片+文本输入，生成文本回答
  - 用途：图像描述、视觉问答、多模态对话等

**本服务需要使用 `Qwen2-VL-7B-Instruct` 生成模型！**

---

## 系统要求

### 硬件要求

- **GPU**: 推荐 NVIDIA GPU，显存 >= 16GB (对于 7B 模型)
  - 使用 bfloat16: ~14GB 显存
  - 使用 float16: ~14GB 显存
  - 使用 float32: ~28GB 显存
- **CPU**: 多核处理器（如果使用 CPU 推理）
- **内存**: >= 32GB RAM
- **存储**: >= 50GB 可用空间（用于模型下载）

### 软件要求

- **操作系统**: Linux (Ubuntu 20.04+), Windows (WSL2), macOS
- **Python**: >= 3.8
- **CUDA**: >= 11.8 (如果使用 GPU)
- **PyTorch**: >= 2.0.0

---

## 安装步骤

### 1. 克隆或进入项目目录

```bash
cd /home/adamliao/Qwen3-VL-Embedding/api
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

或手动安装：

```bash
pip install fastapi uvicorn python-multipart pillow torch transformers qwen-vl-utils
```

### 3. 准备模型

#### 选项 A: 自动下载 (推荐)

服务启动时会自动从 HuggingFace 下载 `Qwen/Qwen2-VL-7B-Instruct`。

**加速下载（可选）**:

```bash
# 使用镜像源
export HF_ENDPOINT=https://hf-mirror.com
```

#### 选项 B: 手动下载

```bash
# 使用 huggingface-cli
pip install huggingface-hub
huggingface-cli download Qwen/Qwen2-VL-7B-Instruct --local-dir ./models/Qwen2-VL-7B-Instruct

# 或使用 git-lfs
git lfs install
git clone https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct ./models/Qwen2-VL-7B-Instruct
```

然后设置环境变量：

```bash
export QWEN_MODEL_PATH="/path/to/Qwen2-VL-7B-Instruct"
```

---

## 启动服务

### 方法 1: 使用启动脚本 (推荐)

```bash
cd /home/adamliao/Qwen3-VL-Embedding/api
./start_service.sh
```

### 方法 2: 直接启动

```bash
cd /home/adamliao/Qwen3-VL-Embedding/api
python -m api.server
```

### 方法 3: 使用 uvicorn (生产环境)

```bash
cd /home/adamliao/Qwen3-VL-Embedding/api
uvicorn api.server:app --host 0.0.0.0 --port 8000 --workers 1
```

### 方法 4: 后台运行

```bash
cd /home/adamliao/Qwen3-VL-Embedding/api
nohup python -m api.server > server.log 2>&1 &
```

查看日志：

```bash
tail -f api/server.log
```

停止服务：

```bash
ps aux | grep "api.server"
kill <PID>
```

---

## 使用服务

### 1. 验证服务

```bash
# 健康检查
curl http://localhost:8000/health

# 模型信息
curl http://localhost:8000/info
```

### 2. API 文档

访问自动生成的 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. 运行测试脚本

```bash
cd /home/adamliao/Qwen3-VL-Embedding/api
python test_service.py
```

### 4. 运行示例代码

```bash
cd /home/adamliao/Qwen3-VL-Embedding/api
python example_usage.py
```

### 5. 交互式测试

```bash
python test_service.py interactive
```

---

## API 使用示例

### Python 客户端

```python
import requests

# 1. 文本推理
response = requests.post(
    "http://localhost:8000/v1/text-inference",
    json={
        "prompt": "什么是深度学习？",
        "max_new_tokens": 512,
        "temperature": 0.7
    }
)
print(response.json()['response'])

# 2. 图片推理
with open("image.jpg", "rb") as f:
    response = requests.post(
        "http://localhost:8000/v1/image-inference",
        files={"image": f},
        data={
            "prompt": "描述这张图片",
            "max_new_tokens": 512
        }
    )
print(response.json()['response'])
```

### cURL 示例

```bash
# 文本推理
curl -X POST http://localhost:8000/v1/text-inference \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "什么是人工智能？",
    "max_new_tokens": 512
  }'

# 图片推理
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@/path/to/image.jpg" \
  -F "prompt=描述这张图片"
```

---

## 故障排除

### 问题 1: 服务无法启动

**症状**: 运行 `python -m api.server` 后报错

**可能原因及解决方案**:

1. **缺少依赖**
   ```bash
   pip install -r api/requirements.txt
   ```

2. **模型路径错误**
   ```bash
   # 检查环境变量
   echo $QWEN_MODEL_PATH
   
   # 或让服务自动下载
   unset QWEN_MODEL_PATH
   ```

3. **端口被占用**
   ```bash
   # 查找占用端口的进程
   lsof -i :8000
   
   # 杀死进程
   kill <PID>
   
   # 或使用其他端口
   uvicorn api.server:app --port 8001
   ```

### 问题 2: CUDA 内存不足

**症状**: `RuntimeError: CUDA out of memory`

**解决方案**:

1. **降低精度**
   ```python
   # 在 server.py 中修改
   torch_dtype="float16"  # 或 "bfloat16"
   ```

2. **使用 CPU**
   ```python
   device="cpu"
   ```

3. **减少批大小**（如果批处理）

### 问题 3: 模型下载慢或失败

**解决方案**:

```bash
# 使用镜像源
export HF_ENDPOINT=https://hf-mirror.com

# 或手动下载后设置路径
export QWEN_MODEL_PATH="/path/to/model"
```

### 问题 4: 推理返回空结果

**可能原因**:

1. **使用了错误的模型**
   - 确保使用 `Qwen2-VL-7B-Instruct` 而不是 `Qwen3-VL-Embedding-8B`

2. **输入格式错误**
   - 检查图片格式（支持: jpg, png, webp等）
   - 检查 prompt 是否为空

### 问题 5: 图片处理失败

**症状**: `Error in processing vision info`

**解决方案**:

1. **检查图片格式**
   ```python
   from PIL import Image
   img = Image.open("image.jpg").convert("RGB")
   img.save("image_converted.jpg")
   ```

2. **检查图片大小**
   ```bash
   # 压缩大图片
   convert input.jpg -resize 1280x1280 output.jpg
   ```

3. **检查 qwen-vl-utils 版本**
   ```bash
   pip install --upgrade qwen-vl-utils
   ```

---

## 代码修复说明

本次修复主要解决以下问题：

### 1. 修复 `inference.py` 中的 `generate()` 函数

**问题**:
- 使用了错误的模型类型（嵌入模型而非生成模型）
- `process_vision_info` 调用方式不正确
- 缺少正确的文本生成逻辑

**修复**:
- 改用 `Qwen2VLForConditionalGeneration` 模型
- 修正了视觉信息处理流程
- 实现了正确的 `generate()` 方法

### 2. 修复 `qwen3_vl_embedding.py` 中的 `process()` 函数

**问题**:
- `_preprocess_inputs()` 批处理逻辑有误
- 视觉信息处理不完整
- 缺少错误处理

**修复**:
- 改进了批处理逻辑，正确处理多个对话
- 完善了图片和视频的处理流程
- 添加了 try-except 错误处理
- 改进了降级处理（fallback）

### 3. 更新 `server.py` 配置

**修复**:
- 添加了模型路径环境变量支持
- 改用正确的生成模型
- 改进了错误提示

---

## 性能优化建议

### 1. 使用 Flash Attention 2

```bash
pip install flash-attn
```

在 `server.py` 中启用：

```python
attn_implementation="flash_attention_2"
```

### 2. 批处理推理

对于多个请求，可以实现批处理以提高吞吐量。

### 3. 模型量化

使用量化模型减少显存占用：

```python
from transformers import BitsAndBytesConfig

quantization_config = BitsAndBytesConfig(
    load_in_4bit=True,
    bnb_4bit_compute_dtype=torch.bfloat16
)
```

### 4. 使用 vLLM (高级)

对于大规模部署，考虑使用 vLLM 加速推理。

---

## 安全建议

1. **网络安全**
   - 生产环境不要暴露到公网
   - 使用反向代理（Nginx）
   - 启用 HTTPS

2. **认证授权**
   - 添加 API Key 验证
   - 实现访问频率限制

3. **输入验证**
   - 限制图片大小
   - 过滤敏感内容

---

## 支持

如有问题，请查看：

- [Qwen2-VL 官方文档](https://github.com/QwenLM/Qwen2-VL)
- [Transformers 文档](https://huggingface.co/docs/transformers)
- [FastAPI 文档](https://fastapi.tiangolo.com/)

---

## 许可证

遵循 Qwen 模型的许可协议。
