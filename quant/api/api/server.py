"""
Qwen3-VL FastAPI 服务器
提供远程推理接口
"""

import json
import logging
import os
import re
import time
from typing import Optional, List
from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, Query, Request
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

# 全局API密钥
API_KEY: Optional[str] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    管理应用生命周期
    启动时加载模型，关闭时释放资源
    """
    global inference_engine, API_KEY

    # 启动事件：加载API密钥
    API_KEY = os.environ.get("API_KEY")
    if API_KEY:
        logger.info("API key authentication enabled")
    else:
        logger.warning("API_KEY not set - service will be unprotected! Set API_KEY environment variable to enable authentication.")

    # 启动事件：加载模型
    logger.info("Starting up - Loading Qwen3-VL model...")
    try:
        # 从环境变量获取模型路径，如果没有则使用默认值
        model_path = os.environ.get(
            "QWEN_MODEL_PATH", 
            "Qwen/Qwen3-VL-8B-Instruct"  # 默认使用HuggingFace模型
        )
        
        logger.info(f"Loading model from: {model_path}")
        
        # 注意：对于文本生成，需要使用Qwen3-VL-8B-Instruct而不是Embedding模型
        # 如果要使用本地模型，请设置环境变量：
        # export QWEN_MODEL_PATH="/path/to/Qwen3-VL-8B-Instruct"
        quantization = os.environ.get("QWEN_QUANTIZATION", None)  # '8bit', '4bit', or None

        inference_engine = Qwen3VLInference(
            model_name_or_path=model_path,
            torch_dtype="bfloat16",
            attn_implementation=None,  # 使用默认实现，如果有flash-attn可以设为"flash_attention_2"
            quantization=quantization,
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


# API密钥验证依赖
async def verify_api_key(api_key: Optional[str] = Query(None, description="API key for authentication")):
    """
    验证API密钥
    
    Args:
        api_key: 从查询参数获取的API密钥（可选）
        
    Raises:
        HTTPException: 如果API密钥无效或未设置
    """
    global API_KEY
    
    # 如果未设置API_KEY，跳过验证（向后兼容，但不推荐）
    if API_KEY is None:
        logger.warning("API_KEY not configured - allowing request without authentication")
        return
    
    # 如果设置了API_KEY但请求中没有提供，拒绝请求
    if api_key is None:
        logger.warning("API key required but not provided in request")
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide api_key as a query parameter."
        )
    
    # 验证API密钥
    if api_key != API_KEY:
        logger.warning(f"Invalid API key attempt from client")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key. Please provide a valid api_key query parameter."
        )
    
    return api_key


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
        "model": "Qwen3-VL-8B-Instruct",
        "status": "ready",
        "device": str(inference_engine.device) if hasattr(inference_engine.device, '__str__') else inference_engine.device,
        "dtype": str(inference_engine.torch_dtype),
    }


@app.post("/v1/text-inference", response_model=TextInferenceResponse)
async def text_inference(request: TextInferenceRequest, _: None = Depends(verify_api_key)):
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
    _: None = Depends(verify_api_key),
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
async def image_inference_base64(request: dict, _: None = Depends(verify_api_key)):
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
    _: None = Depends(verify_api_key),
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


def parse_json_from_response(text: str) -> Optional[dict]:
    """从模型输出中提取第一个JSON对象（支持markdown代码块）"""
    match = re.search(r'\{.*?\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


@app.post("/v1/multi-image-inference")
async def multi_image_inference(
    request: Request,
    _: None = Depends(verify_api_key),
):
    """
    多图推理端点

    Form inputs:
        image_0, image_1, ... (file): 图片文件（至少一张）
        prompt (str): 文本提示
        max_new_tokens (int, optional): 默认256
        temperature (float, optional): 默认0.7
        top_p (float, optional): 默认0.8

    Returns:
        {"status": "success", "response": <str>}
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    form = await request.form()

    pil_images = []
    for i in range(10):
        key = f"image_{i}"
        if key in form:
            upload = form[key]
            contents = await upload.read()
            pil_images.append(Image.open(io.BytesIO(contents)).convert("RGB"))

    if not pil_images:
        raise HTTPException(status_code=400, detail="No image files provided (use image_0, image_1, ...)")

    prompt = form.get("prompt", "Describe these images.")
    max_new_tokens = int(form.get("max_new_tokens", 256))
    temperature = float(form.get("temperature", 0.7))
    top_p = float(form.get("top_p", 0.8))

    logger.info(f"[/v1/multi-image-inference] {len(pil_images)} images, prompt={prompt!r}")

    try:
        response_text = inference_engine.generate_multi_image(
            prompt=prompt,
            images=pil_images,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        elapsed = time.time() - start_time
        logger.info(f"[/v1/multi-image-inference] done in {elapsed:.2f}s")
        return {"status": "success", "response": response_text}
    except Exception as e:
        logger.error(f"[/v1/multi-image-inference] error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/chat")
async def chat_inference(request: dict, _: None = Depends(verify_api_key)):
    """
    Multi-turn chat endpoint with image support.

    Accepts a messages array with optional base64 images.
    Images are referenced by key in each message's "images" list
    and provided as base64 strings in a top-level "images" dict.

    Request JSON:
    {
        "messages": [
            {"role": "user", "content": "prompt", "images": ["img_0"]},
            {"role": "assistant", "content": "response"},
            {"role": "user", "content": "follow-up", "images": ["img_1"]}
        ],
        "images": {"img_0": "<base64>", "img_1": "<base64>"},
        "max_new_tokens": 256,
        "temperature": 0.1,
        "top_p": 0.9
    }

    Returns:
        {"status": "success", "response": <str>}
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    raw_messages = request.get("messages", [])
    image_data = request.get("images", {})  # key -> base64 string
    max_new_tokens = int(request.get("max_new_tokens", 256))
    temperature = float(request.get("temperature", 0.1))
    top_p = float(request.get("top_p", 0.9))

    if not raw_messages:
        raise HTTPException(status_code=400, detail="messages list is required")

    # Decode all base64 images upfront
    pil_images = {}
    for key, b64_str in image_data.items():
        try:
            pil_images[key] = Qwen3VLInference.decode_base64_to_image(b64_str)
        except Exception as e:
            raise HTTPException(
                status_code=400, detail=f"Failed to decode image '{key}': {e}"
            )

    # Build Qwen3-VL format messages
    qwen_messages = []
    for msg in raw_messages:
        role = msg.get("role", "user")
        text = msg.get("content", "")
        msg_image_keys = msg.get("images", [])

        content = []
        for img_key in msg_image_keys:
            if img_key in pil_images:
                content.append({"type": "image", "image": pil_images[img_key]})
        content.append({"type": "text", "text": text})

        qwen_messages.append({"role": role, "content": content})

    logger.info(
        f"[/v1/chat] {len(qwen_messages)} turns, {len(pil_images)} images"
    )

    try:
        response_text = inference_engine.generate_from_messages(
            messages=qwen_messages,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            top_p=top_p,
        )
        elapsed = time.time() - start_time
        logger.info(f"[/v1/chat] done in {elapsed:.2f}s")
        return {"status": "success", "response": response_text}
    except Exception as e:
        logger.error(f"[/v1/chat] error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


VLM_OBJECT_DETECT_PROMPT = (
    "Analyze this image and list all visible objects with details.\n"
    "Respond with JSON only:\n"
    '{"objects": [\n'
    '  {"name": "...", "confidence": 0.0-1.0, "context": "spatial description"}\n'
    '], "room_type": "...", "description": "one sentence"}\n'
    "List up to 8 objects. confidence: how certain the object is present.\n"
    "context: where in the scene (on the table, near the door, etc.).\n"
    "Only JSON, nothing else."
)


@app.post("/v1/object-detect")
async def object_detect(
    image: UploadFile = File(...),
    _: None = Depends(verify_api_key),
):
    """
    Structured object extraction from image.

    Returns:
        {"status": "success", "description": str, "room_type": str,
         "objects": [{"name": str, "confidence": float, "context": str}]}
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    contents = await image.read()
    pil_image = Image.open(io.BytesIO(contents)).convert("RGB")

    logger.info("[/v1/object-detect] processing image")

    try:
        response_text = inference_engine.generate(
            prompt=VLM_OBJECT_DETECT_PROMPT,
            image=pil_image,
            max_new_tokens=300,
            temperature=0.1,
            top_p=0.9,
        )
        elapsed = time.time() - start_time
        logger.info(f"[/v1/object-detect] done in {elapsed:.2f}s")

        parsed = parse_json_from_response(response_text)
        if parsed is None:
            return {
                "status": "success",
                "description": "",
                "room_type": "",
                "objects": [],
                "raw_response": response_text,
            }

        # Validate and normalize objects list
        raw_objects = parsed.get("objects", [])
        valid_objects = []
        for obj in raw_objects:
            if isinstance(obj, dict) and "name" in obj:
                valid_objects.append({
                    "name": str(obj["name"]).lower(),
                    "confidence": float(obj.get("confidence", 0.5)),
                    "context": str(obj.get("context", "")),
                })

        return {
            "status": "success",
            "description": parsed.get("description", ""),
            "room_type": parsed.get("room_type", ""),
            "objects": valid_objects,
        }
    except Exception as e:
        logger.error(f"[/v1/object-detect] error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/detect")
async def detect(
    image: UploadFile = File(...),
    instruction: str = Form(...),
    _: None = Depends(verify_api_key),
):
    """
    VLN检测端点：检测目标物体/位置是否可见

    Form inputs:
        image (file): 当前相机帧
        instruction (str): 语言导航指令（如 "find the red mug"）

    Returns:
        {"found": bool, "bbox": [x1, y1, x2, y2] or null, "confidence": float}
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    contents = await image.read()
    pil_image = Image.open(io.BytesIO(contents)).convert("RGB")

    prompt = (
        f"You are a robot navigation assistant.\n"
        f"Instruction: '{instruction}'\n"
        f"Look at the camera image. Is the target object/location clearly visible?\n\n"
        f"If YES: respond with JSON {{\"found\": true, \"bbox\": [x1, y1, x2, y2], \"confidence\": 0.0-1.0}}\n"
        f"If NO:  respond with JSON {{\"found\": false, \"confidence\": 0.0}}\n"
        f"Only output the JSON, nothing else."
    )

    logger.info(f"[/detect] instruction={instruction!r}")

    try:
        response_text = inference_engine.generate(
            prompt=prompt,
            image=pil_image,
            max_new_tokens=128,
            temperature=0.1,
            top_p=0.9,
        )
        elapsed = time.time() - start_time
        logger.info(f"[/detect] response={response_text!r} in {elapsed:.2f}s")

        parsed = parse_json_from_response(response_text)
        if parsed is None:
            return {"found": False, "bbox": None, "confidence": 0.0}

        found = bool(parsed.get("found", False))
        confidence = float(parsed.get("confidence", 0.0))
        bbox = parsed.get("bbox", None)
        if bbox is not None and (not isinstance(bbox, list) or len(bbox) != 4):
            bbox = None

        return {"found": found, "bbox": bbox, "confidence": confidence}
    except Exception as e:
        logger.error(f"[/detect] error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/confirm_arrival")
async def confirm_arrival(
    image: UploadFile = File(...),
    instruction: str = Form(...),
    _: None = Depends(verify_api_key),
):
    """
    VLN到达确认端点

    Form inputs:
        image (file): 当前相机帧
        instruction (str): 语言导航指令

    Returns:
        {"arrived": bool, "reason": str}
    """
    if inference_engine is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    start_time = time.time()

    contents = await image.read()
    pil_image = Image.open(io.BytesIO(contents)).convert("RGB")

    prompt = (
        f"You are a robot navigation assistant.\n"
        f"Instruction: '{instruction}'\n"
        f"The robot is now close to something. Has the navigation goal been reached?\n"
        f"Respond with JSON {{\"arrived\": true/false, \"reason\": \"...\"}}\n"
        f"Only output the JSON, nothing else."
    )

    logger.info(f"[/confirm_arrival] instruction={instruction!r}")

    try:
        response_text = inference_engine.generate(
            prompt=prompt,
            image=pil_image,
            max_new_tokens=128,
            temperature=0.1,
            top_p=0.9,
        )
        elapsed = time.time() - start_time
        logger.info(f"[/confirm_arrival] response={response_text!r} in {elapsed:.2f}s")

        parsed = parse_json_from_response(response_text)
        if parsed is None:
            return {"arrived": False, "reason": "Failed to parse model response"}

        arrived = bool(parsed.get("arrived", False))
        reason = str(parsed.get("reason", ""))
        return {"arrived": arrived, "reason": reason}
    except Exception as e:
        logger.error(f"[/confirm_arrival] error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # 启动服务器
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )
