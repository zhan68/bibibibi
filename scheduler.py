import subprocess
import time
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 1. 网页服务逻辑：用于唤醒 Render 并通过端口检查 ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot Cluster is Active")

def run_health_check_server():
    # Render 会自动注入 PORT 环境变量，默认使用 10000
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f"[{time.strftime('%X')}] 唤醒服务已启动，监听端口: {port}")
    server.serve_forever()

# --- 2. 核心调度逻辑：每 15 分钟运行一个脚本 ---
def run_robot_loop():
    # 这里填入你所有的脚本文件名
    scripts = ["hao123.py", "hao456.py", "hao789.py", "hao888.py"]
    
    print(f"[{time.strftime('%X')}] 调度器已启动，准备轮询 {len(scripts)} 个脚本...")
    
    while True:
        for script in scripts:
            print(f"\n{'='*30}")
            print(f"[{time.strftime('%X')}] 🚀 开始执行任务: {script}")
            print(f"{'='*30}")
            
            try:
                # 运行脚本并等待其结束
                result = subprocess.run(["python", script], capture_output=True, text=True)
                print(result.stdout)
                if result.stderr:
                    print(f"脚本报错输出: {result.stderr}")
            except Exception as e:
                print(f"调度执行异常: {e}")
            
            print(f"[{time.strftime('%X')}] ✅ {script} 执行完毕。等待 15 分钟...")
            # 休息 900 秒 (15 分钟)
            time.sleep(900)

if __name__ == "__main__":
    # 启动后台唤醒服务器
    threading.Thread(target=run_health_check_server, daemon=True).start()
    
    # 启动循环任务
    run_robot_loop()
