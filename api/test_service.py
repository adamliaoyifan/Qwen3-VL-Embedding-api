"""
测试 Qwen3-VL 推理服务
"""

import requests
import json
import base64
from pathlib import Path
from PIL import Image
import io


class Qwen3VLClient:
    """Qwen3-VL 推理服务客户端"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
    
    def health_check(self):
        """健康检查"""
        response = requests.get(f"{self.base_url}/health")
        return response.json()
    
    def model_info(self):
        """获取模型信息"""
        response = requests.get(f"{self.base_url}/info")
        return response.json()
    
    def text_inference(self, prompt: str, max_new_tokens: int = 512, 
                      temperature: float = 0.7, top_p: float = 0.8):
        """纯文本推理"""
        url = f"{self.base_url}/v1/text-inference"
        data = {
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        response = requests.post(url, json=data)
        return response.json()
    
    def image_inference(self, image_path: str, prompt: str, 
                       max_new_tokens: int = 512, temperature: float = 0.7, 
                       top_p: float = 0.8):
        """图片+文本推理 (文件上传)"""
        url = f"{self.base_url}/v1/image-inference"
        
        with open(image_path, 'rb') as f:
            files = {'image': f}
            data = {
                'prompt': prompt,
                'max_new_tokens': max_new_tokens,
                'temperature': temperature,
                'top_p': top_p
            }
            response = requests.post(url, files=files, data=data)
        
        return response.json()
    
    def image_inference_base64(self, image_path: str, prompt: str,
                              max_new_tokens: int = 512, temperature: float = 0.7,
                              top_p: float = 0.8):
        """图片+文本推理 (Base64编码)"""
        url = f"{self.base_url}/v1/image-inference-base64"
        
        # 读取图片并转换为base64
        with open(image_path, 'rb') as f:
            image_bytes = f.read()
            image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        data = {
            "image_base64": image_base64,
            "prompt": prompt,
            "max_new_tokens": max_new_tokens,
            "temperature": temperature,
            "top_p": top_p
        }
        
        response = requests.post(url, json=data)
        return response.json()
    
    def image_url_inference(self, image_url: str, prompt: str,
                           max_new_tokens: int = 512, temperature: float = 0.7,
                           top_p: float = 0.8):
        """图片+文本推理 (URL)"""
        url = f"{self.base_url}/v1/image-url-inference"
        
        data = {
            'image_url': image_url,
            'prompt': prompt,
            'max_new_tokens': max_new_tokens,
            'temperature': temperature,
            'top_p': top_p
        }
        
        response = requests.post(url, data=data)
        return response.json()


def test_service():
    """测试服务"""
    print("=" * 80)
    print("Qwen3-VL 推理服务测试")
    print("=" * 80)
    
    client = Qwen3VLClient()
    
    # # 1. 健康检查
    # print("\n[1] 健康检查...")
    # try:
    #     result = client.health_check()
    #     print(f"✓ 服务状态: {result}")
    # except Exception as e:
    #     print(f"✗ 健康检查失败: {e}")
    #     print("\n请确保服务已启动:")
    #     print("  cd api && python -m api.server")
    #     return
    
    # # 2. 模型信息
    # print("\n[2] 获取模型信息...")
    # try:
    #     result = client.model_info()
    #     print(f"✓ 模型信息:")
    #     for key, value in result.items():
    #         print(f"  - {key}: {value}")
    # except Exception as e:
    #     print(f"✗ 获取模型信息失败: {e}")
    
    # # 3. 文本推理
    # print("\n[3] 测试文本推理...")
    # try:
    #     result = client.text_inference(
    #         prompt="请用一句话解释什么是人工智能",
    #         max_new_tokens=100,
    #         temperature=0.7
    #     )
    #     print(f"✓ 推理状态: {result['status']}")
    #     print(f"✓ 生成结果:\n{result['response']}")
    # except Exception as e:
    #     print(f"✗ 文本推理失败: {e}")
    
    # 4. 图片推理 (如果有示例图片)
    print("\n[4] 测试图片推理...")
    
    # 查找示例图片
    example_images = [
        "../data/examples/0.jpeg",
        "../data/examples/1.jpg",
        "./test_image.jpg",
    ]
    
    test_image = None
    for img_path in example_images:
        if Path(img_path).exists():
            test_image = img_path
            break
    
    if test_image:
        try:
            result = client.image_inference(
                image_path=test_image,
                prompt="请详细描述这张图片的内容",
                max_new_tokens=200,
                temperature=0.7
            )
            print(f"✓ 推理状态: {result['status']}")
            print(f"✓ 生成结果:\n{result['response']}")
        except Exception as e:
            print(f"✗ 图片推理失败: {e}")
    else:
        print("⚠ 未找到示例图片，跳过图片推理测试")
        print("  可以将图片保存为 test_image.jpg 来测试")
    
    # # 5. Base64 图片推理
    # if test_image:
    #     print("\n[5] 测试 Base64 图片推理...")
    #     try:
    #         result = client.image_inference_base64(
    #             image_path=test_image,
    #             prompt="这张图片的主要内容是什么？",
    #             max_new_tokens=150
    #         )
    #         print(f"✓ 推理状态: {result['status']}")
    #         print(f"✓ 生成结果:\n{result['response']}")
    #     except Exception as e:
    #         print(f"✗ Base64 图片推理失败: {e}")
    
    # 6. URL 图片推理
    # print("\n[6] 测试 URL 图片推理...")
    # try:
    #     # 使用一个公开的测试图片URL
    #     result = client.image_url_inference(
    #         image_url="https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen-VL/assets/demo.jpeg",
    #         prompt="Describe this image in English",
    #         max_new_tokens=200
    #     )
    #     print(f"✓ 推理状态: {result['status']}")
    #     print(f"✓ 生成结果:\n{result['response']}")
    # except Exception as e:
    #     print(f"✗ URL 图片推理失败: {e}")
    
    print("\n" + "=" * 80)
    print("测试完成!")
    print("=" * 80)


def interactive_test():
    """交互式测试"""
    client = Qwen3VLClient()
    
    print("=" * 80)
    print("Qwen3-VL 交互式测试")
    print("=" * 80)
    print("\n命令:")
    print("  text <prompt>          - 文本推理")
    print("  image <path> <prompt>  - 图片推理")
    print("  quit                   - 退出")
    print()
    
    while True:
        try:
            user_input = input("\n> ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'quit':
                break
            
            parts = user_input.split(maxsplit=2)
            command = parts[0].lower()
            
            if command == 'text':
                if len(parts) < 2:
                    print("用法: text <prompt>")
                    continue
                
                prompt = ' '.join(parts[1:])
                print(f"\n生成中...")
                result = client.text_inference(prompt, max_new_tokens=512)
                print(f"\n回答:\n{result['response']}")
            
            elif command == 'image':
                if len(parts) < 3:
                    print("用法: image <path> <prompt>")
                    continue
                
                image_path = parts[1]
                prompt = parts[2]
                
                if not Path(image_path).exists():
                    print(f"错误: 图片不存在: {image_path}")
                    continue
                
                print(f"\n生成中...")
                result = client.image_inference(image_path, prompt, max_new_tokens=512)
                print(f"\n回答:\n{result['response']}")
            
            else:
                print(f"未知命令: {command}")
        
        except KeyboardInterrupt:
            print("\n\n再见!")
            break
        except Exception as e:
            print(f"错误: {e}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "interactive":
        interactive_test()
    else:
        test_service()
