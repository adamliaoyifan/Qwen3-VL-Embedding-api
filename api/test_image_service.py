#!/usr/bin/env python3
"""
Test client for Qwen3-VL Image Inference Service
用于测试Qwen3-VL图片推理服务的客户端
"""

import requests
import json
import base64
import os
import sys
from pathlib import Path

# API服务地址
API_URL = "http://localhost:8000"

def test_health_check():
    """测试健康检查"""
    print("\n" + "="*60)
    print("测试 1: 健康检查")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def test_model_info():
    """测试获取模型信息"""
    print("\n" + "="*60)
    print("测试 2: 获取模型信息")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/info", timeout=5)
        print(f"✓ 状态码: {response.status_code}")
        print(f"✓ 响应: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def test_text_inference():
    """测试纯文本推理"""
    print("\n" + "="*60)
    print("测试 3: 纯文本推理")
    print("="*60)
    
    try:
        payload = {
            "prompt": "请用一句话总结一下机器学习的定义。",
            "max_new_tokens": 128,
            "temperature": 0.7,
            "top_p": 0.8
        }
        
        print(f"请求数据:\n{json.dumps(payload, indent=2, ensure_ascii=False)}\n")
        
        response = requests.post(
            f"{API_URL}/v1/text-inference",
            json=payload,
            timeout=30
        )
        
        print(f"✓ 状态码: {response.status_code}")
        result = response.json()
        print(f"✓ 响应状态: {result.get('status')}")
        print(f"✓ 生成的回答: {result.get('response')}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        return False


def test_image_inference_file(image_path: str):
    """
    测试图片文件推理
    
    Args:
        image_path: 图片文件路径
    """
    print("\n" + "="*60)
    print(f"测试 4: 图片文件推理")
    print(f"图片路径: {image_path}")
    print("="*60)
    
    if not os.path.exists(image_path):
        print(f"✗ 图片文件不存在: {image_path}")
        return False
    
    try:
        # 打开图片文件
        with open(image_path, 'rb') as f:
            files = {'image': (os.path.basename(image_path), f, 'image/jpeg')}
            data = {
                'prompt': '这个图片中有什么？请详细描述。',
                'max_new_tokens': 256,
                'temperature': 0.7,
                'top_p': 0.8
            }
            
            print(f"请求参数:")
            print(f"  - prompt: {data['prompt']}")
            print(f"  - max_new_tokens: {data['max_new_tokens']}\n")
            
            response = requests.post(
                f"{API_URL}/v1/image-inference",
                files=files,
                data=data,
                timeout=60
            )
        
        print(f"✓ 状态码: {response.status_code}")
        result = response.json()
        print(f"✓ 响应状态: {result.get('status')}")
        print(f"✓ 生成的回答:\n{result.get('response')}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_image_inference_base64(image_path: str):
    """
    测试Base64编码的图片推理
    
    Args:
        image_path: 图片文件路径
    """
    print("\n" + "="*60)
    print("测试 5: Base64编码图片推理")
    print(f"图片路径: {image_path}")
    print("="*60)
    
    if not os.path.exists(image_path):
        print(f"✗ 图片文件不存在: {image_path}")
        return False
    
    try:
        # 读取并编码为Base64
        with open(image_path, 'rb') as f:
            image_base64 = base64.b64encode(f.read()).decode('utf-8')
        
        payload = {
            "image_base64": image_base64,
            "prompt": "这个图片展示了什么？",
            "max_new_tokens": 256,
            "temperature": 0.7,
            "top_p": 0.8
        }
        
        print(f"请求参数:")
        print(f"  - prompt: {payload['prompt']}")
        print(f"  - image_base64: {image_base64[:50]}... (长度: {len(image_base64)})\n")
        
        response = requests.post(
            f"{API_URL}/v1/image-inference-base64",
            json=payload,
            timeout=60
        )
        
        print(f"✓ 状态码: {response.status_code}")
        result = response.json()
        print(f"✓ 响应状态: {result.get('status')}")
        print(f"✓ 生成的回答:\n{result.get('response')}")
        return True
    except Exception as e:
        print(f"✗ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


def find_test_image():
    """查找可用的测试图片"""
    possible_paths = [
        "/home/adamliao/Desktop/近照.jpg",
        "/home/adamliao/Desktop/image.jpg",
        "./examples/test_image.jpg",
        "/home/adamliao/Qwen3-VL-Embedding/examples/retrieval_results/images/img_0.jpg",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    
    return None


def main():
    """主函数"""
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + " "*58 + "║")
    print("║" + "  Qwen3-VL 图片推理服务 - 测试客户端".center(58) + "║")
    print("║" + " "*58 + "║")
    print("╚" + "="*58 + "╝")
    
    # 首先测试服务连接
    print(f"\n正在连接服务: {API_URL}")
    if not test_health_check():
        print("\n✗ 无法连接到服务，请确保:")
        print("  1. 服务已启动: python -m uvicorn api.server:app --port 8000")
        print("  2. 服务地址正确: " + API_URL)
        sys.exit(1)
    
    # 测试模型信息
    test_model_info()
    
    # 测试纯文本推理
    test_text_inference()
    
    # 查找测试图片
    test_image_path = find_test_image()
    if test_image_path:
        print(f"\n找到测试图片: {test_image_path}")
        
        # 测试图片文件推理
        test_image_inference_file(test_image_path)
        
        # 测试Base64推理
        test_image_inference_base64(test_image_path)
    else:
        print("\n⚠ 未找到测试图片，跳过图片相关测试")
        print("请提供一个.jpg图片文件进行测试")
    
    print("\n" + "="*60)
    print("✓ 所有测试完成!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
