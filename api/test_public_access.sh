#!/bin/bash
# Test script for public access to Qwen3-VL service

PUBLIC_IP="157.254.192.2"
API_KEY="adamliaoyifan"

echo "=========================================="
echo "Testing Public Access to Qwen3-VL Service"
echo "=========================================="
echo ""

# Test 1: Local health check
echo "[1] Testing local health endpoint..."
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✓ Local server is running"
else
    echo "✗ Local server is not responding"
    exit 1
fi

# Test 2: Local inference with API key
echo ""
echo "[2] Testing local inference endpoint with API key..."
RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/text-inference?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_new_tokens": 10}' \
  --max-time 30)

if echo "$RESPONSE" | grep -q "success"; then
    echo "✓ Local inference works with API key"
    echo "  Response: $(echo $RESPONSE | head -c 100)..."
else
    echo "✗ Local inference failed"
    echo "  Response: $RESPONSE"
fi

# Test 3: Public IP health check
echo ""
echo "[3] Testing public IP health endpoint..."
if curl -s --max-time 10 "http://$PUBLIC_IP:8000/health" > /dev/null; then
    echo "✓ Public IP is accessible"
else
    echo "✗ Public IP is not accessible (firewall/router issue)"
    echo ""
    echo "Troubleshooting steps:"
    echo "  1. Check if server is behind NAT/router"
    echo "  2. Configure port forwarding on router (port 8000)"
    echo "  3. Check firewall: sudo ufw status"
    echo "  4. Check if ISP blocks port 8000"
fi

# Test 4: Public IP inference
echo ""
echo "[4] Testing public IP inference endpoint..."
RESPONSE=$(curl -s -X POST "http://$PUBLIC_IP:8000/v1/text-inference?api_key=$API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello", "max_new_tokens": 10}' \
  --max-time 30)

if echo "$RESPONSE" | grep -q "success"; then
    echo "✓ Public inference works!"
    echo "  Response: $(echo $RESPONSE | head -c 100)..."
else
    echo "✗ Public inference failed"
    echo "  Response: $RESPONSE"
    echo ""
    echo "Possible issues:"
    echo "  - Firewall blocking port 8000"
    echo "  - Router not forwarding port 8000"
    echo "  - ISP blocking the port"
    echo "  - Server not accessible from internet"
fi

echo ""
echo "=========================================="
echo "Test Complete"
echo "=========================================="
echo ""
echo "If public access doesn't work:"
echo "  1. Check firewall: sudo ufw status"
echo "  2. Check port forwarding on router"
echo "  3. Try from a different network/device"
echo "  4. Check server logs for connection attempts"
