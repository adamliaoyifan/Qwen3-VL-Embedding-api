"""
Fixed version of _query_custom_vision function
This demonstrates the correct way to pass API key as a query parameter
"""

import requests
import base64
import cv2


def _query_custom_vision(self, api_url, api_key, cv_image):
    """
    调用自定义VL模型API (使用base64 JSON格式)
    
    Args:
        api_url: API endpoint URL
        api_key: API key (可选，部分接口不需要)
        cv_image: OpenCV格式的图像 (BGR)
    
    Returns:
        bool: 是否检测到票据
    """
    try:
        # 1. 将图像编码为base64
        _, buffer = cv2.imencode('.jpg', cv_image)
        image_base64 = base64.b64encode(buffer).decode('utf-8')
        
        # 2. 构造JSON payload
        payload = {
            "image_base64": image_base64,  # Server expects "image_base64" field
            "prompt": "Is the person holding a ticket, boarding pass, or document? Answer with only YES or NO.",
            "max_new_tokens": 50,
            "temperature": 0.7,
            "top_p": 0.8
        }
        
        # 3. 构造请求头
        headers = {
            "Content-Type": "application/json"
        }
        
        # 4. 使用params传递API key (修复后的代码)
        # 使用params参数而不是手动构造URL，这样可以：
        # - 正确处理URL编码
        # - 处理URL中已有的查询参数
        # - 更安全和可维护
        params = {}
        if api_key:
            params["api_key"] = api_key
        
        # 5. 发送POST请求（JSON格式）
        response = requests.post(
            api_url,
            headers=headers,
            json=payload,
            params=params,  # 使用params参数传递API key
            timeout=10
        )
        response.raise_for_status()
        
        result = response.json()
        
        # 6. 解析返回结果（适配Qwen3-VL的响应格式）
        response_text = ""
        if "response" in result:
            response_text = result["response"]
        elif "result" in result:
            response_text = result["result"]
        elif "has_ticket" in result:
            return result["has_ticket"]
        
        # 7. 从响应文本中判断是否检测到票据
        if response_text:
            response_upper = response_text.upper()
            # 检查是否包含肯定答案
            if "YES" in response_upper or "HOLDING" in response_upper or "TICKET" in response_upper:
                return True
            # 检查是否包含否定答案
            if "NO" in response_upper or "NOT" in response_upper:
                return False
        
        return False
        
    except Exception as e:
        self.get_logger().error(f"Error in custom vision API: {e}")
        return False


# 关键修复点说明：
# ============================================
# 修复前（错误的方式）:
#   if api_key:
#       api_url = api_url + f"?api_key={api_key}"
#   response = requests.post(api_url, ...)
#
# 问题：
# 1. 如果URL已经有查询参数，会破坏URL结构
# 2. 如果api_key包含特殊字符，可能没有正确编码
# 3. 如果api_key是None或空字符串，仍然会尝试添加
#
# 修复后（正确的方式）:
#   params = {}
#   if api_key:
#       params["api_key"] = api_key
#   response = requests.post(api_url, params=params, ...)
#
# 优点：
# 1. requests库会自动处理URL编码
# 2. 正确处理URL中已有的查询参数
# 3. 只在api_key存在时才添加
# 4. 代码更清晰和可维护
# ============================================
