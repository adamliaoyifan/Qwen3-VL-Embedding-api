"""
Qwen3-VL Inference Module
用于处理Qwen3-VL模型的推理逻辑
基于Qwen3VLEmbedder的嵌入模型实现
"""

import torch
import torch.nn.functional as F
import logging
from typing import Optional, Dict, Any, List, Union
from PIL import Image
from io import BytesIO
import base64
import unicodedata
from transformers.models.qwen3_vl.modeling_qwen3_vl import Qwen3VLForConditionalGeneration
from transformers import AutoProcessor, AutoTokenizer, BitsAndBytesConfig
from qwen_vl_utils import process_vision_info

logger = logging.getLogger(__name__)


class Qwen3VLInference:
    """
    Qwen3-VL推理类
    用于文本生成的实现
    """

    def __init__(
        self,
        model_name_or_path: str = "Qwen/Qwen3-VL-8B-Instruct",
        torch_dtype: Optional[str] = "bfloat16",
        attn_implementation: Optional[str] = "flash_attention_2",
        device: Optional[str] = None,
        quantization: Optional[str] = None,
    ):
        """
        初始化推理引擎

        Args:
            model_name_or_path: 模型路径
            torch_dtype: 数据类型 ('bfloat16', 'float16', 'float32')
            attn_implementation: 注意力实现方式
            device: 设备 ('cuda', 'cpu')
            quantization: 量化方式 ('8bit', '4bit', None)
        """
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        logger.info(f"Using device: {self.device}")

        # 设置torch数据类型
        if torch_dtype == "bfloat16":
            self.torch_dtype = torch.bfloat16
        elif torch_dtype == "float16":
            self.torch_dtype = torch.float16
        else:
            self.torch_dtype = torch.float32

        logger.info(f"Loading model from {model_name_or_path} (quantization={quantization})...")

        # 检测是否为本地路径
        import os
        is_local_path = os.path.isdir(model_name_or_path) or os.path.exists(model_name_or_path)

        # 加载processor
        processor_kwargs = {"trust_remote_code": True}
        if is_local_path:
            processor_kwargs["local_files_only"] = True
            logger.info("Loading from local path")

        self.processor = AutoProcessor.from_pretrained(
            model_name_or_path, **processor_kwargs
        )

        # 配置量化
        quantization_config = None
        if quantization == "8bit":
            quantization_config = BitsAndBytesConfig(load_in_8bit=True)
            logger.info("Using 8-bit quantization (BitsAndBytes)")
        elif quantization == "4bit":
            quantization_config = BitsAndBytesConfig(
                load_in_4bit=True,
                bnb_4bit_compute_dtype=self.torch_dtype,
                bnb_4bit_quant_type="nf4",
            )
            logger.info("Using 4-bit NF4 quantization (BitsAndBytes)")

        # 加载模型 - 使用生成模型而不是嵌入模型
        model_kwargs = {
            "trust_remote_code": True,
            "device_map": "auto" if self.device == "cuda" else self.device,
        }
        if quantization_config is not None:
            model_kwargs["quantization_config"] = quantization_config
        else:
            model_kwargs["torch_dtype"] = self.torch_dtype

        if is_local_path:
            model_kwargs["local_files_only"] = True

        if attn_implementation is not None:
            try:
                model_kwargs["attn_implementation"] = attn_implementation
            except Exception as e:
                logger.warning(f"Failed to use {attn_implementation}, using default: {e}")

        self.model = Qwen3VLForConditionalGeneration.from_pretrained(
            model_name_or_path,
            **model_kwargs
        )
        self.model.eval()

        # 配置参数
        self.max_length = 8192
        self.min_pixels = 256 * 28 * 28  # 200704
        self.max_pixels = 1280 * 28 * 28  # 1003520

        logger.info("Model loaded successfully!")

    def format_message(
        self,
        text: str,
        image: Optional[Union[str, Image.Image]] = None,
    ) -> List[Dict]:
        """
        格式化消息为Qwen3-VL的标准格式

        Args:
            text: 文本输入
            image: 图片输入

        Returns:
            格式化的消息列表
        """
        content = []
        
        # 如果有图片，先添加图片
        if image is not None:
            if isinstance(image, Image.Image):
                # PIL Image对象
                content.append({
                    "type": "image",
                    "image": image,
                })
            elif isinstance(image, str):
                # 图片路径或URL
                if image.startswith(('http://', 'https://')):
                    content.append({
                        "type": "image",
                        "image": image,
                    })
                else:
                    # 本地路径
                    content.append({
                        "type": "image",
                        "image": f"file://{image}",
                    })
        
        # 添加文本
        content.append({
            "type": "text",
            "text": text
        })
        
        # 构建消息
        messages = [
            {
                "role": "user",
                "content": content,
            }
        ]
        
        return messages

    def _preprocess_inputs(self, messages: List[Dict]) -> Dict[str, torch.Tensor]:
        """
        预处理输入消息

        Args:
            messages: 消息列表

        Returns:
            预处理后的输入字典
        """
        # 应用聊天模板
        text = self.processor.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # 处理视觉信息
        image_inputs, video_inputs = process_vision_info(messages)
        
        # 使用processor处理所有输入
        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
            min_pixels=self.min_pixels,
            max_pixels=self.max_pixels,
        )
        
        return inputs

    @torch.no_grad()
    def generate(
        self,
        prompt: str,
        image: Optional[Union[str, Image.Image]] = None,
        max_new_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.8,
    ) -> str:
        """
        生成回答

        Args:
            prompt: 输入提示
            image: 输入图片
            max_new_tokens: 最大生成token数
            temperature: 温度参数
            top_p: top_p采样参数

        Returns:
            生成的文本
        """
        try:
            # 格式化消息
            messages = self.format_message(text=prompt, image=image)
            
            # 预处理输入
            inputs = self._preprocess_inputs(messages)
            inputs = inputs.to(self.model.device)
            
            # 生成输出
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
            )
            
            # 只保留生成的部分（去除输入部分）
            generated_ids_trimmed = [
                out_ids[len(in_ids):] 
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]
            
            # 解码生成的文本
            response = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False
            )[0]
            
            return response

        except Exception as e:
            logger.error(f"Error during generation: {e}", exc_info=True)
            raise

    def format_multi_image_message(
        self,
        text: str,
        images: List[Image.Image],
    ) -> List[Dict]:
        """
        格式化多图消息为Qwen3-VL的标准格式

        Args:
            text: 文本输入
            images: PIL Image列表

        Returns:
            格式化的消息列表
        """
        content = []
        for img in images:
            content.append({"type": "image", "image": img})
        content.append({"type": "text", "text": text})

        return [{"role": "user", "content": content}]

    @torch.no_grad()
    def generate_multi_image(
        self,
        prompt: str,
        images: List[Image.Image],
        max_new_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.8,
    ) -> str:
        """
        多图推理生成回答

        Args:
            prompt: 输入提示
            images: PIL Image列表
            max_new_tokens: 最大生成token数
            temperature: 温度参数
            top_p: top_p采样参数

        Returns:
            生成的文本
        """
        try:
            messages = self.format_multi_image_message(text=prompt, images=images)
            inputs = self._preprocess_inputs(messages)
            inputs = inputs.to(self.model.device)

            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
            )

            generated_ids_trimmed = [
                out_ids[len(in_ids):]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            response = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            return response

        except Exception as e:
            logger.error(f"Error during multi-image generation: {e}", exc_info=True)
            raise

    @torch.no_grad()
    def generate_from_messages(
        self,
        messages: List[Dict],
        max_new_tokens: int = 1024,
        temperature: float = 0.7,
        top_p: float = 0.8,
    ) -> str:
        """
        Generate a response from a pre-built multi-turn messages list.

        Messages follow Qwen3-VL format:
        [
            {"role": "user", "content": [{"type": "image", "image": <PIL>}, {"type": "text", "text": "..."}]},
            {"role": "assistant", "content": [{"type": "text", "text": "..."}]},
            {"role": "user", "content": [{"type": "text", "text": "follow-up"}]},
        ]

        Args:
            messages: Multi-turn message list.
            max_new_tokens: Max tokens to generate.
            temperature: Sampling temperature.
            top_p: Top-p sampling parameter.

        Returns:
            Generated text response.
        """
        try:
            inputs = self._preprocess_inputs(messages)
            inputs = inputs.to(self.model.device)

            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=max_new_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=temperature > 0,
            )

            generated_ids_trimmed = [
                out_ids[len(in_ids):]
                for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
            ]

            response = self.processor.batch_decode(
                generated_ids_trimmed,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )[0]

            return response

        except Exception as e:
            logger.error(f"Error during multi-turn generation: {e}", exc_info=True)
            raise

    @staticmethod
    def encode_image_to_base64(image: Image.Image) -> str:
        """
        将PIL Image编码为base64字符串

        Args:
            image: PIL Image对象

        Returns:
            base64编码的字符串
        """
        buffered = BytesIO()
        image.save(buffered, format="JPEG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str

    @staticmethod
    def decode_base64_to_image(img_str: str) -> Image.Image:
        """
        从base64字符串解码为PIL Image

        Args:
            img_str: base64编码的字符串

        Returns:
            PIL Image对象
        """
        img_data = base64.b64decode(img_str)
        img = Image.open(BytesIO(img_data))
        return img
