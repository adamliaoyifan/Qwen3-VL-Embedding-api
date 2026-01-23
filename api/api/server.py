"""
Qwen3-VL FastAPI 服务器
提供远程推理接口
"""

import logging
from typing import Optional
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image
import io

from .inference import Qwen3VLInference

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# 全局推理引擎
inference_engine: Optional[Qwen3VLInference] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理应用生命周期
    启动时加载模型，关闭时释放资源
    """
    global inference_engine

    # 启动事件：加载模型
    logger.info("Starting up - Loading Qwen3-VL model...")
    try:
        import os
        # 从环境变量获取模型路径，如果没有则使用默认值
        model_path = os.environ.get(
            "QWEN_MODEL_PATH", 
            "Qwen/Qwen2-VL-7B-Instruct"  # 默认使用HuggingFace模型
        )
        
        logger.info(f"Loading model from: {model_path}")
        
        # 注意：对于文本生成，需要使用Qwen2-VL-7B-Instruct而不是Embedding模型
        # 如果要使用本地模型，请设置环境变量：
        # export QWEN_MODEL_PATH="/path/to/Qwen2-VL-7B-Instruct"
        inference_engine = Qwen3VLInference(
            model_name_or_path=model_path,
            torch_dtype="bfloat16",
            attn_implementation=None,  # 使用默认实现，如果有flash-attn可以设为"flash_attention_2"
        )
        logger.info("Model loaded successfully!")
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise

    yield

    # 关闭事件：释放资源
    logger.info("Shutting down - Releasing resources...")
    if inference_engine is not None:
        del inference_engine


# 创建FastAPI应用
app = FastAPI(
    title="Qwen3-VL Inference Server",
    description="远程推理服务 - 支持图片和文本输入",
    version="1.0.0",
    lifespan=lifespan,
)

# 添加CORS中间件，允许跨域请求
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境建议指定具体的域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 定义请求/响应模型
class TextInferenceRequest(BaseModel):
    """纯文本推理请求"""

    prompt: str
    max_new_tokens: int = 1024
    temperature: float = 0.7
    top_p: float = 0.8


class TextInferenceResponse(BaseModel):
    """推理响应"""

    status: str
    response: str
    error: Optional[str] = None


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "service": "Qwen3-VL Inference Server"}


@app.get("/info")
async def model_info():
    """获取模型信息"""
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {
        "model": "Qwen2-VL-7B-Instruct",
        "status": "ready",
        "device": str(inference_engine.device) if hasattr(inference_engine.device, '__str__') else inference_engine.device,
        "dtype": str(inference_engine.torch_dtype),
    }


@app.post("/v1/text-inference", response_model=TextInferenceResponse)
async def text_inference(request: TextInferenceRequest):
    """
    纯文本推理端点

    Args:
        request: 包含prompt和生成参数的请求

    Returns:
        推理结果
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        logger.info(f"Processing text inference request: {request.prompt[:100]}...")

        response = inference_engine.generate(
            prompt=request.prompt,
            image=None,
            max_new_tokens=request.max_new_tokens,
            temperature=request.temperature,
            top_p=request.top_p,
        )

        logger.info("Text inference completed successfully")

        return TextInferenceResponse(status="success", response=response)

    except Exception as e:
        logger.error(f"Error during text inference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/image-inference")
async def image_inference(
    image: UploadFile = File(...),
    prompt: str = Form(...),
    max_new_tokens: int = Form(1024),
    temperature: float = Form(0.7),
    top_p: float = Form(0.8),
):
    """
    图片+文本推理端点

    Args:
        image: 上传的图片文件
        prompt: 文本提示
        max_new_tokens: 最大生成token数
        temperature: 生成温度
        top_p: top_p采样参数

    Returns:
        推理结果
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # 读取图片文件
        contents = await image.read()
        pil_image = Image.open(io.BytesIO(contents)).convert("RGB")

        logger.info(f"Processing image inference: {prompt[:100]}...")

        # 执行推理
        response = inference_engine.generate(
            prompt=prompt,
            image=pil_image,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        logger.info("Image inference completed successfully")

        return TextInferenceResponse(status="success", response=response)

    except Exception as e:
        logger.error(f"Error during image inference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/image-inference-base64")
async def image_inference_base64(request: dict):
    """
    支持base64编码图片的推理端点

    Request JSON:
    {
        "image_base64": "...",  # base64编码的图片
        "prompt": "...",
        "max_new_tokens": 1024,
        "temperature": 0.7,
        "top_p": 0.8
    }

    Returns:
        推理结果
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        # 解码base64图片
        image_base64 = request.get("image_base64")
        if not image_base64:
            raise ValueError("image_base64 is required")

        pil_image = Qwen3VLInference.decode_base64_to_image(image_base64)

        prompt = request.get("prompt", "")
        max_new_tokens = request.get("max_new_tokens", 1024)
        temperature = request.get("temperature", 0.7)
        top_p = request.get("top_p", 0.8)

        logger.info(f"Processing image inference (base64): {prompt[:100]}...")

        # 执行推理
        response = inference_engine.generate(
            prompt=prompt,
            image=pil_image,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        logger.info("Image inference (base64) completed successfully")

        return TextInferenceResponse(status="success", response=response)

    except Exception as e:
        logger.error(f"Error during image inference (base64): {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/image-url-inference")
async def image_url_inference(
    image_url: str = Form(...),
    prompt: str = Form(...),
    max_new_tokens: int = Form(1024),
    temperature: float = Form(0.7),
    top_p: float = Form(0.8),
):
    """
    支持图片URL的推理端点

    Args:
        image_url: 图片URL地址
        prompt: 文本提示
        max_new_tokens: 最大生成token数
        temperature: 生成温度
        top_p: top_p采样参数

    Returns:
        推理结果
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    try:
        logger.info(f"Processing image URL inference: {prompt[:100]}...")

        # 执行推理（模型会自动处理URL）
        response = inference_engine.generate(
            prompt=prompt,
            image=image_url,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )

        logger.info("Image URL inference completed successfully")

        return TextInferenceResponse(status="success", response=response)

    except Exception as e:
        logger.error(f"Error during image URL inference: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
