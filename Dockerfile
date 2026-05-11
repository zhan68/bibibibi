FROM python:3.9-slim

# 安装 Chrome 浏览器
RUN apt-get update && apt-get install -y wget gnupg && \
    wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - && \
    sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' && \
    apt-get update && apt-get install -y google-chrome-stable

# 复制你的代码并安装依赖
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

# 启动命令
CMD ["python", "hao123.py"]
