# Qwen3-VL Remote Inference Service

基于 Qwen2-VL 模型的远程推理服务，支持图片和文本输入。

## 重要说明

**注意**: 此服务用于**文本生成**，需要使用 `Qwen2-VL-7B-Instruct` 模型，而不是 `Qwen3-VL-Embedding-8B` 嵌入模型。

- **生成模型** (用于此服务): `Qwen2-VL-7B-Instruct` - 可以根据图片和文本生成回答
- **嵌入模型** (不用于此服务): `Qwen3-VL-Embedding-8B` - 只能生成向量表示，不能生成文本

## 安装依赖

```bash
cd api
pip install fastapi uvicorn python-multipart pillow torch transformers qwen-vl-utils
```

## 模型准备

### 方法1: 使用 HuggingFace 自动下载 (推荐)

服务会自动从 HuggingFace 下载 `Qwen/Qwen2-VL-7B-Instruct` 模型。

### 方法2: 使用本地模型

如果你已经下载了模型到本地，可以设置环境变量:

```bash
export QWEN_MODEL_PATH="/path/to/Qwen2-VL-7B-Instruct"
```

**注意**: 如果你只有 `Qwen3-VL-Embedding-8B`，你需要下载 `Qwen2-VL-7B-Instruct`:

```bash
# 使用 huggingface-cli 下载
huggingface-cli download Qwen/Qwen2-VL-7B-Instruct --local-dir ./models/Qwen2-VL-7B-Instruct

# 或者使用 git
git lfs clone https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct ./models/Qwen2-VL-7B-Instruct
```

## 启动服务

### 基本启动

```bash
cd api
python -m api.server
```

服务将在 `http://0.0.0.0:8000` 启动

### 使用本地模型启动

```bash
export QWEN_MODEL_PATH="/home/adamliao/Qwen3-VL-Embedding/models/Qwen2-VL-7B-Instruct"
cd api
python -m api.server
```

### 使用 uvicorn 启动 (生产环境)

```bash
cd api
uvicorn api.server:app --host 0.0.0.0 --port 8000 --workers 1
```

## API 端点

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

### 2. 模型信息

```bash
curl http://localhost:8000/info
```

### 3. 纯文本推理

```bash
curl -X POST http://localhost:8000/v1/text-inference \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "什么是人工智能？",
    "max_new_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.8
  }'
```

### 4. 图片+文本推理 (文件上传)

```bash
curl -X POST http://localhost:8000/v1/image-inference \
  -F "image=@/path/to/image.jpg" \
  -F "prompt=描述这张图片" \
  -F "max_new_tokens=512" \
  -F "temperature=0.7" \
  -F "top_p=0.8"
```

### 5. 图片+文本推理 (Base64编码)

```bash
curl -X POST http://localhost:8000/v1/image-inference-base64 \
  -H "Content-Type: application/json" \
  -d '{
    "image_base64": "base64_encoded_image_string",
    "prompt": "描述这张图片",
    "max_new_tokens": 512,
    "temperature": 0.7,
    "top_p": 0.8
  }'
```

### 6. 图片+文本推理 (URL)

```bash
curl -X POST http://localhost:8000/v1/image-url-inference \
  -F "image_url=https://example.com/image.jpg" \
  -F "prompt=描述这张图片" \
  -F "max_new_tokens=512" \
  -F "temperature=0.7" \
  -F "top_p=0.8"
```

## Python 客户端示例

```python
import requests
from PIL import Image
import io

# 1. 文本推理
def text_inference(prompt: str):
    url = "http://localhost:8000/v1/text-inference"
    data = {
        "prompt": prompt,
        "max_new_tokens": 512,
        "temperature": 0.7,
        "top_p": 0.8
    }
    response = requests.post(url, json=data)
    return response.json()

# 2. 图片推理
def image_inference(image_path: str, prompt: str):
    url = "http://localhost:8000/v1/image-inference"
    
    with open(image_path, 'rb') as f:
        files = {'image': f}
        data = {
            'prompt': prompt,
            'max_new_tokens': 512,
            'temperature': 0.7,
            'top_p': 0.8
        }
        response = requests.post(url, files=files, data=data)
    
    return response.json()

# 使用示例
if __name__ == "__main__":
    # 文本推理
    result = text_inference("什么是深度学习？")
    print("文本推理结果:", result['response'])
    
    # 图片推理
    result = image_inference("image.jpg", "描述这张图片")
    print("图片推理结果:", result['response'])
```

## 参数说明

- `prompt`: 输入提示文本
- `image`: 图片文件/路径/URL
- `max_new_tokens`: 最大生成token数 (默认: 1024)
- `temperature`: 生成温度，控制随机性 (默认: 0.7, 范围: 0.0-2.0)
  - 0.0: 完全确定性
  - 1.0: 标准随机性
  - 2.0: 高随机性
- `top_p`: nucleus采样参数 (默认: 0.8, 范围: 0.0-1.0)

## 性能优化

### 1. 使用 Flash Attention 2 (可选)

如果已安装 `flash-attn`，可以在 `server.py` 中设置:

```python
inference_engine = Qwen3VLInference(
    model_name_or_path=model_path,
    torch_dtype="bfloat16",
    attn_implementation="flash_attention_2",  # 启用 Flash Attention
)
```

### 2. 多GPU支持

模型会自动使用 `device_map="auto"` 进行多GPU分配。

### 3. 批处理

服务支持单个请求处理，如需批处理可以使用多个客户端并发请求。

## 故障排除

### 问题1: 模型下载慢

使用镜像源:

```bash
export HF_ENDPOINT=https://hf-mirror.com
```

### 问题2: CUDA 内存不足

降低精度或使用 CPU:

```python
# 使用 float16
torch_dtype="float16"

# 或使用 CPU
device="cpu"
```

### 问题3: 生成结果为空或错误

确保使用的是**生成模型** (`Qwen2-VL-7B-Instruct`) 而不是嵌入模型。

## 文件说明

- `api/server.py`: FastAPI 服务器
- `api/inference.py`: 推理引擎
- `test_service.py`: 测试脚本
- `example_usage.py`: 使用示例

## License

遵循 Qwen 模型的许可协议。
