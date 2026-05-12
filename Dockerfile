# 使用集成了 Chrome 浏览器的 Python 镜像
FROM python:3.11-slim

# 安装 Chrome 和基础依赖
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    google-chrome-stable \
    --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 先复制依赖文件并安装
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制当前目录下所有脚本
COPY . .

# 设置环境变量，确保 Selenium 能找到 Chrome
ENV CHROME_BIN=/usr/bin/google-chrome
ENV PYTHONUNBUFFERED=1

# 启动命令：直接运行你的主程序
CMD ["python", "123.py"]
