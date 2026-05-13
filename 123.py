import subprocess
import time
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Cluster Active")

def run_server():
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f">>> [System] 健康检查服务器已启动")
    server.serve_forever()

def run_robot_loop():
    scripts = ["hao123.py", "hao456.py", "hao789.py", "hao888.py", "hao999.py"]
    while True:
        for script in scripts:
            print(f"\n--- [🕒 {time.strftime('%X')}] 准备执行: {script} ---")
            success = False
            try:
                # 5分钟超时保护
                subprocess.run(["python", script], timeout=300, check=True) 
                print(f"--- [✅] {script} 正常结束 ---")
                success = True
            except Exception as e:
                print(f"--- [❌] {script} 发生故障: {e} ---")
            
            # 智能跳过逻辑：成功休眠15分钟，失败仅休眠2分钟
            wait_time = 900 if success else 120
            print(f">>> [System] 休息 {wait_time} 秒后继续...")
            time.sleep(wait_time)

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    run_robot_loop()
