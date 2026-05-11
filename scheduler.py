import subprocess
import time
import os
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- 1. 必须有的网页服务，用来告诉 Render “我活着的” ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")

def run_health_check_server():
    # Render 会自动分配端口给环境变量 PORT，默认是 10000
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"检测服务器启动在端口: {port}")
    server.serve_forever()

# --- 2. 你的机器人调度逻辑 ---
def run_robot_loop():
    scripts = ["hao123.py", "hao456.py", "hao789.py", "hao888.py"]
    while True:
        for script in scripts:
            print(f"正在启动机器人: {script}")
            # 使用 subprocess 运行你的爬虫
            subprocess.run(["python", script])
            # 运行完一个，休息 15 分钟
            print(f"等待 15 分钟...")
            time.sleep(900)

if __name__ == "__main__":
    # 启动健康检查服务器（放在后台线程）
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    # 启动机器人循环
    run_robot_loop()
