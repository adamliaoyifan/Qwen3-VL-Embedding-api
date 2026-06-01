#!/usr/bin/env python3
"""
Simple example: How to use Qwen3-VL image inference service
简单示例：如何使用Qwen3-VL图片推理服务
"""

import requests
import json
import os
from pathlib import Path

# ============================================================
# 配置
# ============================================================
API_URL = "http://localhost:8000"
IMAGE_PATH = "/home/adamliao/Desktop/近照.jpg"  # 修改为你的图片路径
API_KEY = os.environ.get("API_KEY")  # 从环境变量获取API密钥

# ============================================================
# 示例 1: 上传 .jpg 文件进行推理
# ============================================================
def example_1_image_file_inference():
    """使用图片文件进行推理"""
    print("\n" + "="*60)
    print("示例 1: 上传 .jpg 文件进行推理")
    print("="*60)
    
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ 图片不存在: {IMAGE_PATH}")
        return
    
    # 打开图片文件
    with open(IMAGE_PATH, 'rb') as f:
        files = {'image': f}
        data = {
            'prompt': '这个图片中有什么？请详细描述。',
            'max_new_tokens': 256,
            'temperature': 0.7,
            'top_p': 0.8
        }
        
        print(f"📤 发送请求:")
        print(f"   - 图片: {IMAGE_PATH}")
        print(f"   - 提示: {data['prompt']}")
        print(f"   - 最大tokens: {data['max_new_tokens']}\n")
        
        params = {}
        if API_KEY:
            params["api_key"] = API_KEY
        
        try:
            response = requests.post(
                f"{API_URL}/v1/image-inference",
                files=files,
                data=data,
                params=params,
                timeout=120
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ 推理成功!")
                print(f"📝 AI的回答:\n{result['response']}")
            else:
                print(f"❌ 错误: {response.status_code}")
                print(f"   {response.text}")
        except Exception as e:
            print(f"❌ 请求失败: {e}")


# ============================================================
# 示例 2: 多张图片批量处理
# ============================================================
def example_2_batch_processing():
    """批量处理多张图片"""
    print("\n" + "="*60)
    print("示例 2: 批量处理多张图片")
    print("="*60)
    
    # 查找示例图片目录
    images_dir = Path("/home/adamliao/Qwen3-VL-Embedding/examples/retrieval_results/images")
    if not images_dir.exists():
        print(f"❌ 图片目录不存在: {images_dir}")
        return
    
    # 获取所有jpg文件
    jpg_files = list(images_dir.glob("*.jpg"))[:3]  # 只处理前3张
    
    if not jpg_files:
        print(f"❌ 目录中没有jpg文件")
        return
    
    print(f"📂 找到 {len(jpg_files)} 张图片\n")
    
    prompts = [
        "这个图片中有什么对象？",
        "请描述这张图片的主要内容。",
        "这个场景看起来是什么时候拍摄的？"
    ]
    
    for i, image_path in enumerate(jpg_files):
        print(f"处理图片 {i+1}/{len(jpg_files)}: {image_path.name}")
        
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'prompt': prompts[i % len(prompts)],
                'max_new_tokens': 128,
            }
            
            params = {}
            if API_KEY:
                params["api_key"] = API_KEY
            
            try:
                response = requests.post(
                    f"{API_URL}/v1/image-inference",
                    files=files,
                    data=data,
                    params=params,
                    timeout=120
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"  ✅ {result['response'][:100]}...\n")
                else:
                    print(f"  ❌ 错误: {response.status_code}\n")
            except Exception as e:
                print(f"  ❌ 请求失败: {e}\n")


# ============================================================
# 示例 3: 使用 Base64 编码进行推理
# ============================================================
def example_3_base64_inference():
    """使用 Base64 编码的图片进行推理"""
    print("\n" + "="*60)
    print("示例 3: 使用 Base64 编码进行推理")
    print("="*60)
    
    if not os.path.exists(IMAGE_PATH):
        print(f"❌ 图片不存在: {IMAGE_PATH}")
        return
    
    import base64
    
    # 读取并编码为 Base64
    with open(IMAGE_PATH, 'rb') as f:
        image_base64 = base64.b64encode(f.read()).decode('utf-8')
    
    print(f"📤 发送Base64编码的图片")
    print(f"   - Base64长度: {len(image_base64)} 字符\n")
    
    payload = {
        "image_base64": image_base64,
        "prompt": "这个图片中的主要特征是什么？",
        "max_new_tokens": 256,
        "temperature": 0.7,
        "top_p": 0.8
    }
    
    params = {}
    if API_KEY:
        params["api_key"] = API_KEY
    
    try:
        response = requests.post(
            f"{API_URL}/v1/image-inference-base64",
            json=payload,
            params=params,
            timeout=120
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 推理成功!")
            print(f"📝 AI的回答:\n{result['response']}")
        else:
            print(f"❌ 错误: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")


# ============================================================
# 示例 4: 纯文本推理
# ============================================================
def example_4_text_inference():
    """纯文本推理（不使用图片）"""
    print("\n" + "="*60)
    print("示例 4: 纯文本推理")
    print("="*60)
    
    payload = {
        "prompt": "请用一句话解释什么是深度学习。",
        "max_new_tokens": 128,
        "temperature": 0.7,
        "top_p": 0.8
    }
    
    print(f"📤 发送纯文本请求")
    print(f"   - 提示: {payload['prompt']}\n")
    
    params = {}
    if API_KEY:
        params["api_key"] = API_KEY
    
    try:
        response = requests.post(
            f"{API_URL}/v1/text-inference",
            json=payload,
            params=params,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 推理成功!")
            print(f"📝 AI的回答:\n{result['response']}")
        else:
            print(f"❌ 错误: {response.status_code}")
            print(f"   {response.text}")
    except Exception as e:
        print(f"❌ 请求失败: {e}")


# ============================================================
# 示例 5: 检查服务健康状态
# ============================================================
def example_5_health_check():
    """检查服务是否正常运行"""
    print("\n" + "="*60)
    print("示例 5: 检查服务健康状态")
    print("="*60)
    
    try:
        # 检查健康状态
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务正常运行")
            print(f"   {response.json()}")
        else:
            print(f"❌ 服务异常: {response.status_code}")
            return False
        
        # 获取模型信息
        response = requests.get(f"{API_URL}/info", timeout=5)
        if response.status_code == 200:
            print("\n✅ 模型信息:")
            info = response.json()
            for key, value in info.items():
                print(f"   - {key}: {value}")
        else:
            print(f"❌ 获取模型信息失败: {response.status_code}")
            return False
        
        return True
    except Exception as e:
        print(f"❌ 服务连接失败: {e}")
        print(f"   请确保服务已启动: python -m uvicorn api.server:app --port 8000")
        return False


# ============================================================
# 主函数
# ============================================================
def main():
    """主函数"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  Qwen3-VL 图片推理服务 - 使用示例".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    # 首先检查服务
    if not example_5_health_check():
        return
    
    # 运行示例
    example_1_image_file_inference()
    example_4_text_inference()
    example_3_base64_inference()
    example_2_batch_processing()
    
    print("\n" + "="*60)
    print("✓ 所有示例完成!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
