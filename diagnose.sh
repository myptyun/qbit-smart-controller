#!/bin/bash

# 诊断脚本 - 检查配置文件和容器状态

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

CONTAINER_NAME="qbit-smart-controller"
CONFIG_DIR="/home/myptyun/config"
DATA_DIR="/home/myptyun/data"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}🔍 容器和配置诊断工具${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# 1. 检查宿主机配置文件
echo -e "${YELLOW}[1/8] 检查宿主机配置文件${NC}"
if [ -f "$CONFIG_DIR/config.yaml" ]; then
    echo -e "${GREEN}✅ 配置文件存在${NC}"
    echo -e "   路径: $CONFIG_DIR/config.yaml"
    echo -e "   大小: $(du -h $CONFIG_DIR/config.yaml | cut -f1)"
    echo -e "   权限: $(ls -la $CONFIG_DIR/config.yaml | awk '{print $1, $3, $4}')"
    echo ""
    echo -e "${BLUE}配置文件前10行:${NC}"
    head -n 10 "$CONFIG_DIR/config.yaml" | sed 's/^/   /'
    echo ""
else
    echo -e "${RED}❌ 配置文件不存在: $CONFIG_DIR/config.yaml${NC}"
    echo ""
fi

# 2. 检查容器状态
echo -e "${YELLOW}[2/8] 检查容器状态${NC}"
if docker ps -f name=$CONTAINER_NAME | grep -q $CONTAINER_NAME; then
    echo -e "${GREEN}✅ 容器正在运行${NC}"
    docker ps -f name=$CONTAINER_NAME --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo ""
else
    echo -e "${RED}❌ 容器未运行${NC}"
    echo ""
fi

# 3. 检查容器内的配置文件
echo -e "${YELLOW}[3/8] 检查容器内的配置文件${NC}"
if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
    if docker exec $CONTAINER_NAME test -f /app/config/config.yaml; then
        echo -e "${GREEN}✅ 容器内配置文件存在${NC}"
        echo -e "   路径: /app/config/config.yaml"
        docker exec $CONTAINER_NAME ls -lh /app/config/config.yaml | awk '{print "   权限:", $1, $3, $4, "大小:", $5}'
        echo ""
        echo -e "${BLUE}容器内配置文件前10行:${NC}"
        docker exec $CONTAINER_NAME head -n 10 /app/config/config.yaml 2>/dev/null | sed 's/^/   /' || echo -e "${RED}   无法读取容器内配置文件${NC}"
        echo ""
    else
        echo -e "${RED}❌ 容器内配置文件不存在${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠️  容器未运行，跳过检查${NC}"
    echo ""
fi

# 4. 检查卷挂载
echo -e "${YELLOW}[4/8] 检查卷挂载${NC}"
if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
    echo -e "${BLUE}挂载点信息:${NC}"
    docker inspect $CONTAINER_NAME --format='{{range .Mounts}}  {{.Type}}: {{.Source}} -> {{.Destination}} ({{if .RW}}读写{{else}}只读{{end}}){{println}}{{end}}'
    echo ""
else
    echo -e "${YELLOW}⚠️  容器未运行，跳过检查${NC}"
    echo ""
fi

# 5. 查看容器日志（最后20行）
echo -e "${YELLOW}[5/8] 查看容器日志（最后20行）${NC}"
if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
    docker logs --tail 20 $CONTAINER_NAME 2>&1 | sed 's/^/   /'
    echo ""
else
    echo -e "${YELLOW}⚠️  容器未运行，检查最后的日志${NC}"
    docker logs --tail 20 $CONTAINER_NAME 2>&1 | sed 's/^/   /' || echo -e "${RED}   无法获取日志${NC}"
    echo ""
fi

# 6. 测试配置文件语法
echo -e "${YELLOW}[6/8] 测试配置文件YAML语法${NC}"
if command -v python3 &> /dev/null; then
    python3 -c "
import yaml
import sys
try:
    with open('$CONFIG_DIR/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    print('   ✅ YAML 语法正确')
    print('   包含配置项:')
    for key in config.keys():
        print(f'      - {key}')
except Exception as e:
    print(f'   ❌ YAML 语法错误: {e}')
    sys.exit(1)
" 2>&1
    echo ""
else
    echo -e "${YELLOW}   ⚠️  Python3 未安装，跳过YAML语法检查${NC}"
    echo ""
fi

# 7. 检查qBittorrent连接
echo -e "${YELLOW}[7/8] 检查qBittorrent配置${NC}"
if [ -f "$CONFIG_DIR/config.yaml" ]; then
    echo -e "${BLUE}从配置文件提取qBittorrent信息:${NC}"
    grep -A 5 "qbittorrent_instances:" "$CONFIG_DIR/config.yaml" | sed 's/^/   /'
    echo ""
fi

# 8. 测试健康检查
echo -e "${YELLOW}[8/8] 测试服务健康状态${NC}"
if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
    if curl -f http://localhost:5000/health > /dev/null 2>&1; then
        echo -e "${GREEN}✅ 健康检查通过${NC}"
        curl -s http://localhost:5000/health | python3 -m json.tool 2>/dev/null || curl -s http://localhost:5000/health
        echo ""
    else
        echo -e "${RED}❌ 健康检查失败${NC}"
        echo ""
    fi
else
    echo -e "${YELLOW}⚠️  容器未运行，无法测试${NC}"
    echo ""
fi

# 建议
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}💡 诊断建议${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if [ ! -f "$CONFIG_DIR/config.yaml" ]; then
    echo -e "${RED}🔴 问题: 宿主机配置文件不存在${NC}"
    echo -e "   解决方案:"
    echo -e "   1. 运行初始化脚本: ${BLUE}./init_config.sh${NC}"
    echo -e "   2. 或手动创建配置文件"
    echo ""
fi

if docker ps -q -f name=$CONTAINER_NAME > /dev/null 2>&1; then
    if ! docker exec $CONTAINER_NAME test -f /app/config/config.yaml 2>/dev/null; then
        echo -e "${RED}🔴 问题: 容器内无法访问配置文件${NC}"
        echo -e "   解决方案:"
        echo -e "   1. 检查卷挂载是否正确"
        echo -e "   2. 重启容器: ${BLUE}docker restart $CONTAINER_NAME${NC}"
        echo ""
    fi
    
    # 检查是否使用只读挂载
    if docker inspect $CONTAINER_NAME --format='{{range .Mounts}}{{if eq .Destination "/app/config"}}{{.RW}}{{end}}{{end}}' 2>/dev/null | grep -q "false"; then
        echo -e "${RED}🔴 问题: 配置目录是只读挂载${NC}"
        echo -e "   解决方案:"
        echo -e "   1. 停止容器: ${BLUE}docker stop $CONTAINER_NAME${NC}"
        echo -e "   2. 删除容器: ${BLUE}docker rm $CONTAINER_NAME${NC}"
        echo -e "   3. 重新启动时移除 :ro 标志"
        echo ""
    fi
fi

echo -e "${GREEN}诊断完成！${NC}"
echo ""
echo -e "${YELLOW}📝 如果发现问题:${NC}"
echo -e "   1. 查看上面的诊断信息"
echo -e "   2. 根据建议修复问题"
echo -e "   3. 重启容器: ${BLUE}docker restart $CONTAINER_NAME${NC}"
echo -e "   4. 查看FAQ.md了解更多: ${BLUE}cat FAQ.md${NC}"
echo ""

