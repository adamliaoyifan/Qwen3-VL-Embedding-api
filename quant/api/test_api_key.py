#!/usr/bin/env python3
"""
Test script to verify API key authentication is working correctly
"""

import requests
import os
import base64
from PIL import Image
import io

API_URL = "http://localhost:8000"
API_KEY = os.environ.get("API_KEY")

def test_without_api_key():
    """Test request without API key - should fail if API_KEY is set"""
    print("\n" + "="*60)
    print("Test 1: Request WITHOUT API key")
    print("="*60)
    
    payload = {
        "image_base64": "dummy_base64_string",
        "prompt": "Test prompt",
        "max_new_tokens": 10
    }
    
    try:
        response = requests.post(
            f"{API_URL}/v1/image-inference-base64",
            json=payload,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 401:
            print("✓ Correctly rejected request without API key")
        elif response.status_code == 200:
            print("⚠ Request accepted - API_KEY might not be set on server")
        else:
            print(f"⚠ Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")


def test_with_api_key():
    """Test request with API key"""
    print("\n" + "="*60)
    print("Test 2: Request WITH API key (using params)")
    print("="*60)
    
    if not API_KEY:
        print("⚠ API_KEY environment variable not set")
        print("   Set it with: export API_KEY='your-key-here'")
        return
    
    print(f"Using API_KEY: {API_KEY[:10]}..." if len(API_KEY) > 10 else f"Using API_KEY: {API_KEY}")
    
    payload = {
        "image_base64": "dummy_base64_string",
        "prompt": "Test prompt",
        "max_new_tokens": 10
    }
    
    # Use params (correct way)
    params = {"api_key": API_KEY}
    
    try:
        response = requests.post(
            f"{API_URL}/v1/image-inference-base64",
            json=payload,
            params=params,  # API key as query parameter
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 401:
            print("✗ Request rejected - API key might be incorrect")
            print(f"Response: {response.text}")
        elif response.status_code == 200:
            print("✓ Request accepted with API key")
        elif response.status_code == 500:
            print("⚠ Server error (expected for dummy image, but auth passed)")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"✗ Error: {e}")


def test_wrong_method():
    """Test that GET method is not allowed"""
    print("\n" + "="*60)
    print("Test 3: GET request (should be 405 Method Not Allowed)")
    print("="*60)
    
    params = {}
    if API_KEY:
        params["api_key"] = API_KEY
    
    try:
        response = requests.get(
            f"{API_URL}/v1/image-inference-base64",
            params=params,
            timeout=5
        )
        print(f"Status Code: {response.status_code}")
        if response.status_code == 405:
            print("✓ Correctly rejected GET request (must use POST)")
        else:
            print(f"⚠ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")


def check_server_config():
    """Check if server has API_KEY configured"""
    print("\n" + "="*60)
    print("Server Configuration Check")
    print("="*60)
    
    try:
        # Health check doesn't need API key
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✓ Server is running")
            print(f"  Response: {response.json()}")
        else:
            print(f"⚠ Server returned: {response.status_code}")
    except Exception as e:
        print(f"✗ Cannot connect to server: {e}")
        print(f"  Make sure server is running at {API_URL}")


if __name__ == "__main__":
    print("\n" + "╔" + "="*58 + "╗")
    print("║" + "  API Key Authentication Test".center(58) + "║")
    print("╚" + "="*58 + "╝")
    
    check_server_config()
    test_without_api_key()
    test_with_api_key()
    test_wrong_method()
    
    print("\n" + "="*60)
    print("Summary:")
    print("="*60)
    print("1. If Test 1 passes (401), server has API_KEY set")
    print("2. If Test 2 passes (200/500), API key authentication works")
    print("3. If Test 3 shows 405, endpoint correctly requires POST")
    print("\nTo set API key on server:")
    print("  export API_KEY='your-secret-key'")
    print("  python -m api.server")
    print("\nTo set API key for client:")
    print("  export API_KEY='your-secret-key'")
    print("  python test_api_key.py")
