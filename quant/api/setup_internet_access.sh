#!/bin/bash

# Qwen3-VL Internet Access Setup Script
# This script helps configure your server for internet access

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================"
echo "Qwen3-VL Internet Access Setup"
echo "========================================"
echo ""

# Step 1: Get IP addresses
echo "[1/5] Finding your IP addresses..."
echo ""

PUBLIC_IP=$(curl -s ifconfig.me 2>/dev/null || curl -s ipinfo.io/ip 2>/dev/null || echo "Unable to determine")
LOCAL_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "Unable to determine")

echo -e "${BLUE}Public IP:${NC} $PUBLIC_IP"
echo -e "${BLUE}Local IP:${NC} $LOCAL_IP"
echo ""

# Step 2: Check if service is running
echo "[2/5] Checking service status..."
echo ""

if pgrep -f "api.server" > /dev/null; then
    echo -e "${GREEN}✓ Service is running${NC}"
    SERVICE_RUNNING=true
else
    echo -e "${YELLOW}⚠ Service is not running${NC}"
    SERVICE_RUNNING=false
fi

# Check if port is listening
if netstat -tuln 2>/dev/null | grep -q ":8000 " || ss -tuln 2>/dev/null | grep -q ":8000 "; then
    LISTENING=$(netstat -tuln 2>/dev/null | grep ":8000 " || ss -tuln 2>/dev/null | grep ":8000 ")
    if echo "$LISTENING" | grep -q "0.0.0.0:8000"; then
        echo -e "${GREEN}✓ Port 8000 is listening on all interfaces (0.0.0.0)${NC}"
    else
        echo -e "${YELLOW}⚠ Port 8000 is listening but may not be on all interfaces${NC}"
    fi
else
    echo -e "${RED}✗ Port 8000 is not listening${NC}"
fi
echo ""

# Step 3: Check firewall
echo "[3/5] Checking firewall configuration..."
echo ""

if command -v ufw &> /dev/null; then
    if sudo ufw status | grep -q "Status: active"; then
        if sudo ufw status | grep -q "8000/tcp"; then
            echo -e "${GREEN}✓ UFW firewall is active and port 8000 is allowed${NC}"
        else
            echo -e "${YELLOW}⚠ UFW firewall is active but port 8000 is NOT allowed${NC}"
            echo ""
            read -p "Do you want to allow port 8000? (y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                sudo ufw allow 8000/tcp
                echo -e "${GREEN}✓ Port 8000 has been allowed${NC}"
            fi
        fi
    else
        echo -e "${YELLOW}⚠ UFW firewall is inactive${NC}"
        echo "You may want to enable it for security: sudo ufw enable"
    fi
elif command -v firewall-cmd &> /dev/null; then
    if sudo firewall-cmd --list-ports 2>/dev/null | grep -q "8000/tcp"; then
        echo -e "${GREEN}✓ Firewalld allows port 8000${NC}"
    else
        echo -e "${YELLOW}⚠ Firewalld does not allow port 8000${NC}"
        read -p "Do you want to allow port 8000? (y/n) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            sudo firewall-cmd --permanent --add-port=8000/tcp
            sudo firewall-cmd --reload
            echo -e "${GREEN}✓ Port 8000 has been allowed${NC}"
        fi
    fi
else
    echo -e "${YELLOW}⚠ No common firewall detected (ufw/firewalld)${NC}"
    echo "You may need to configure iptables manually"
fi
echo ""

# Step 4: Test local access
echo "[4/5] Testing local access..."
echo ""

if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Service is accessible locally${NC}"
    HEALTH_RESPONSE=$(curl -s http://localhost:8000/health)
    echo "  Response: $HEALTH_RESPONSE"
else
    echo -e "${RED}✗ Service is NOT accessible locally${NC}"
    echo "  Make sure the service is running: python -m api.server"
fi
echo ""

# Step 5: Summary and instructions
echo "[5/5] Summary and Access Information"
echo "========================================"
echo ""

if [ "$SERVICE_RUNNING" = true ]; then
    echo -e "${GREEN}Service Status: Running${NC}"
else
    echo -e "${RED}Service Status: Not Running${NC}"
    echo ""
    echo "To start the service:"
    echo "  cd /home/adamliao/Qwen3-VL-Embedding/api"
    echo "  python -m api.server"
    echo ""
fi

echo ""
echo "Access URLs:"
echo "  Local:        http://localhost:8000"
if [ "$LOCAL_IP" != "Unable to determine" ]; then
    echo "  Local Network: http://$LOCAL_IP:8000"
fi
if [ "$PUBLIC_IP" != "Unable to determine" ]; then
    echo "  Internet:     http://$PUBLIC_IP:8000"
fi
echo ""
echo "API Documentation:"
if [ "$PUBLIC_IP" != "Unable to determine" ]; then
    echo "  Swagger UI:    http://$PUBLIC_IP:8000/docs"
    echo "  ReDoc:        http://$PUBLIC_IP:8000/redoc"
else
    echo "  Swagger UI:    http://localhost:8000/docs"
    echo "  ReDoc:        http://localhost:8000/redoc"
fi
echo ""

# Router port forwarding instructions
echo "========================================"
echo "Router Configuration (if behind NAT)"
echo "========================================"
echo ""
echo "If your server is behind a router, you need to configure port forwarding:"
echo ""
echo "1. Log into your router admin panel"
echo "   (Usually at http://192.168.1.1 or http://192.168.0.1)"
echo ""
echo "2. Find 'Port Forwarding' or 'Virtual Server' section"
echo ""
echo "3. Add a new rule:"
echo "   - Service Name: Qwen3-VL"
echo "   - External Port: 8000"
echo "   - Internal IP: $LOCAL_IP"
echo "   - Internal Port: 8000"
echo "   - Protocol: TCP"
echo ""
echo "4. Save and apply"
echo ""

# Test from internet
echo "========================================"
echo "Testing Internet Access"
echo "========================================"
echo ""
echo "To test from another machine:"
if [ "$PUBLIC_IP" != "Unable to determine" ]; then
    echo "  curl http://$PUBLIC_IP:8000/health"
else
    echo "  curl http://YOUR_PUBLIC_IP:8000/health"
fi
echo ""

# Security reminder
echo "========================================"
echo "Security Reminder"
echo "========================================"
echo ""
echo -e "${YELLOW}⚠ Important:${NC} Your service is now accessible from the internet!"
echo ""
echo "For production use, consider:"
echo "  1. Adding API authentication (see INTERNET_ACCESS.md)"
echo "  2. Using HTTPS with Nginx reverse proxy"
echo "  3. Configuring rate limiting"
echo "  4. Restricting access to specific IPs"
echo ""
echo "See INTERNET_ACCESS.md for detailed security configuration."
echo ""

# Quick commands
echo "========================================"
echo "Quick Commands"
echo "========================================"
echo ""
echo "Start service:"
echo "  cd /home/adamliao/Qwen3-VL-Embedding/api"
echo "  python -m api.server"
echo ""
echo "Start in background:"
echo "  nohup python -m api.server > server.log 2>&1 &"
echo ""
echo "Check service:"
echo "  curl http://localhost:8000/health"
echo "  curl http://localhost:8000/info"
echo ""
echo "View logs (if using nohup):"
echo "  tail -f server.log"
echo ""

echo -e "${GREEN}Setup complete!${NC}"
echo ""
