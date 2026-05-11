import subprocess
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
import threading

# --- 网页服务部分：应对 Render 的端口检查 ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running...")

def run_web_server():
    # Render 会自动分配端口到环境变量 PORT
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), SimpleHandler)
    server.serve_forever()

# --- 机器人调度部分 ---
def run_robot_loop():
    scripts = ["hao123.py", "hao456.py", "hao789.py", "hao888.py"]
    while True:
        for script in scripts:
            print(f"正在启动: {script}")
            subprocess.run(["python", script])
            time.sleep(900)  # 等待 15 分钟

if __name__ == "__main__":
    # 开启网页服务线程
    threading.Thread(target=run_web_server, daemon=True).start()
    # 开启机器人循环
    run_robot_loop()
