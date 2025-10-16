FROM python:3.11-slim

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TZ=Asia/Shanghai

WORKDIR /app

# 设置时区
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    # 基础工具
    curl \
    wget \
    ca-certificates \
    # Git版本管理
    git \
    # 时区支持
    tzdata \
    # 网络和SSL支持
    openssl \
    # 系统库
    libc6 \
    libssl3 \
    libffi8 \
    # Python编译依赖
    build-essential \
    python3-dev \
    # 其他常用工具
    procps \
    htop \
    nano \
    vim \
    # 清理缓存
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY version.py ./
COPY test_qb_simple.py ./
COPY test_qb_connection.py ./
COPY test_qb_container.py ./
COPY .git/ ./.git/

# 生成版本信息文件（在构建时）
RUN python version.py > /dev/null 2>&1 || true && \
    python -c "from version import get_version_info; import json; \
    with open('version_info.json', 'w') as f: \
    json.dump(get_version_info(), f)" && \
    rm -rf ./.git

# 创建必要的目录
RUN mkdir -p /app/data/logs /app/data/config /app/config

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 暴露端口
EXPOSE 5000

# 运行应用

CMD ["python", "-u", "app/main.py"]
