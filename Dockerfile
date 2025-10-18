# 使用Python 3.9官方镜像
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 复制requirements.txt并安装Python依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建必要的目录
RUN mkdir -p data/logs config

# 暴露端口
EXPOSE 5000

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# 启动命令
CMD ["python", "app/main.py"]