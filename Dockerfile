FROM python:3.9-slim

# 安装 Chrome 所需的依赖和浏览器本体
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    fonts-liberation \
    libasound2 \
    libnss3 \
    libx11-6 \
    libxcomposite1 \
    libxdamage1 \
    libxrandr2 \
    xdg-utils \
    --no-install-recommends && \
    wget -q -O /tmp/chrome.deb https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt-get install -y /tmp/chrome.deb && \
    rm /tmp/chrome.deb && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .
RUN pip install --no-cache-dir -r requirements.txt

# 启动你的脚本
CMD ["python", "hao123.py"]
