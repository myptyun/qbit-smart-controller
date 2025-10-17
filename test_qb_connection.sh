#!/bin/bash

# qBittorrent 连接测试脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔍 qBittorrent 连接测试${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 从配置文件读取 QB 信息
CONFIG_FILE="/home/myptyun/config/config.yaml"

if [ ! -f "$CONFIG_FILE" ]; then
    echo -e "${RED}❌ 配置文件不存在: $CONFIG_FILE${NC}"
    exit 1
fi

# 提取 QB 配置（使用简单的 grep）
QB_HOST=$(grep -A 5 "qbittorrent_instances:" "$CONFIG_FILE" | grep "host:" | head -1 | awk '{print $2}' | tr -d '"')
QB_USER=$(grep -A 5 "qbittorrent_instances:" "$CONFIG_FILE" | grep "username:" | head -1 | awk '{print $2}' | tr -d '"')
QB_PASS=$(grep -A 5 "qbittorrent_instances:" "$CONFIG_FILE" | grep "password:" | head -1 | awk '{print $2}' | tr -d '"')

echo -e "${BLUE}配置信息:${NC}"
echo -e "   Host: $QB_HOST"
echo -e "   Username: $QB_USER"
echo -e "   Password: ${QB_PASS:0:3}***"
echo ""

# 1. 测试基本连接
echo -e "${YELLOW}[1/5] 测试基本连接${NC}"
if curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$QB_HOST" | grep -q "200\|401\|403"; then
    echo -e "${GREEN}✅ 服务器可访问${NC}"
else
    echo -e "${RED}❌ 服务器不可访问${NC}"
    echo -e "   请检查: $QB_HOST"
    exit 1
fi
echo ""

# 2. 测试 API 端点
echo -e "${YELLOW}[2/5] 测试 API 端点${NC}"
API_VERSION_URL="$QB_HOST/api/v2/app/webapiVersion"
VERSION_RESPONSE=$(curl -s "$API_VERSION_URL")
if [ -n "$VERSION_RESPONSE" ]; then
    echo -e "${GREEN}✅ API 端点可访问${NC}"
    echo -e "   WebAPI 版本: $VERSION_RESPONSE"
else
    echo -e "${RED}❌ API 端点不可访问${NC}"
fi
echo ""

# 3. 测试登录（详细模式）
echo -e "${YELLOW}[3/5] 测试登录认证${NC}"
LOGIN_URL="$QB_HOST/api/v2/auth/login"

echo -e "${BLUE}登录请求:${NC}"
echo -e "   URL: $LOGIN_URL"
echo -e "   Method: POST"
echo -e "   Data: username=$QB_USER&password=***"
echo ""

# 执行登录请求并保存响应
RESPONSE=$(curl -v -X POST "$LOGIN_URL" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$QB_USER&password=$QB_PASS" \
    --cookie-jar /tmp/qb_cookies.txt \
    2>&1)

# 检查响应状态
if echo "$RESPONSE" | grep -q "HTTP.*200"; then
    echo -e "${GREEN}✅ 登录请求成功 (HTTP 200)${NC}"
    
    # 检查响应内容
    LOGIN_CONTENT=$(echo "$RESPONSE" | tail -1)
    echo -e "   响应内容: $LOGIN_CONTENT"
    
    if [ "$LOGIN_CONTENT" = "Ok." ]; then
        echo -e "${GREEN}✅ 登录认证成功${NC}"
    else
        echo -e "${YELLOW}⚠️  响应内容异常: $LOGIN_CONTENT${NC}"
    fi
    
    # 检查 Set-Cookie 头
    if echo "$RESPONSE" | grep -q "Set-Cookie.*SID="; then
        SID=$(echo "$RESPONSE" | grep "Set-Cookie.*SID=" | sed 's/.*SID=\([^;]*\).*/\1/')
        echo -e "${GREEN}✅ 获取到 SID Cookie: ${SID:0:20}...${NC}"
    else
        echo -e "${RED}❌ 未获取到 SID Cookie${NC}"
        echo -e "${BLUE}Set-Cookie 头信息:${NC}"
        echo "$RESPONSE" | grep -i "Set-Cookie" | sed 's/^/   /'
    fi
else
    echo -e "${RED}❌ 登录请求失败${NC}"
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP" | tail -1)
    echo -e "   HTTP 状态: $HTTP_CODE"
    
    if echo "$RESPONSE" | grep -q "403"; then
        echo -e "${YELLOW}💡 可能原因:${NC}"
        echo -e "   - 用户名或密码错误"
        echo -e "   - IP 地址被封禁"
        echo -e "   - 需要在 qBittorrent 设置中启用 'Bypass authentication for clients on localhost'"
    elif echo "$RESPONSE" | grep -q "401"; then
        echo -e "${YELLOW}💡 可能原因:${NC}"
        echo -e "   - 用户名或密码错误"
    fi
fi
echo ""

# 4. 测试带 Cookie 的请求
echo -e "${YELLOW}[4/5] 测试带 Cookie 的 API 请求${NC}"
if [ -f /tmp/qb_cookies.txt ] && grep -q "SID" /tmp/qb_cookies.txt; then
    TRANSFER_URL="$QB_HOST/api/v2/transfer/info"
    TRANSFER_RESPONSE=$(curl -s -b /tmp/qb_cookies.txt "$TRANSFER_URL")
    
    if [ -n "$TRANSFER_RESPONSE" ] && echo "$TRANSFER_RESPONSE" | grep -q "dl_info_speed"; then
        echo -e "${GREEN}✅ 带 Cookie 的请求成功${NC}"
        echo -e "   响应示例: $(echo "$TRANSFER_RESPONSE" | head -c 100)..."
    else
        echo -e "${RED}❌ 带 Cookie 的请求失败${NC}"
        echo -e "   响应: $TRANSFER_RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠️  跳过：未获取到有效的 Cookie${NC}"
fi
echo ""

# 5. 测试容器内的连接
echo -e "${YELLOW}[5/5] 测试容器内的连接${NC}"
if docker ps -q -f name=qbit-smart-controller > /dev/null 2>&1; then
    echo -e "${BLUE}从容器内测试连接:${NC}"
    
    # 测试网络连通性
    if docker exec qbit-smart-controller curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$QB_HOST" | grep -q "200\|401\|403"; then
        echo -e "${GREEN}✅ 容器可以访问 qBittorrent${NC}"
    else
        echo -e "${RED}❌ 容器无法访问 qBittorrent${NC}"
        echo -e "${YELLOW}💡 如果 qBittorrent 在同一机器上，尝试:${NC}"
        echo -e "   - 使用 http://172.17.0.1:8080 (Docker 默认网关)"
        echo -e "   - 使用 http://host.docker.internal:8080"
    fi
else
    echo -e "${YELLOW}⚠️  容器未运行，跳过测试${NC}"
fi
echo ""

# 清理临时文件
rm -f /tmp/qb_cookies.txt

# 总结
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}📊 测试总结${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

echo -e "${YELLOW}建议检查项:${NC}"
echo ""
echo -e "1. ${BLUE}qBittorrent 设置${NC}"
echo -e "   - 工具 → 选项 → Web UI"
echo -e "   - 确认 Web UI 已启用"
echo -e "   - 确认用户名和密码正确"
echo -e "   - 如果需要，启用 'Bypass authentication for clients on localhost'"
echo ""
echo -e "2. ${BLUE}网络配置${NC}"
echo -e "   - 检查 qBittorrent 监听的IP和端口"
echo -e "   - 如果在同一机器，使用 Docker 网关 IP"
echo -e "   - 检查防火墙规则"
echo ""
echo -e "3. ${BLUE}容器配置${NC}"
echo -e "   - 确保已重新构建镜像: ${GREEN}docker build -t qbit-controller .${NC}"
echo -e "   - 确保容器使用最新镜像"
echo -e "   - 查看容器日志: ${GREEN}docker logs qbit-smart-controller${NC}"
echo ""
echo -e "4. ${BLUE}配置文件${NC}"
echo -e "   - 编辑: ${GREEN}nano /home/myptyun/config/config.yaml${NC}"
echo -e "   - 确认 host、username、password 正确"
echo -e "   - 重启容器: ${GREEN}docker restart qbit-smart-controller${NC}"
echo ""

