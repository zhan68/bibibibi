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
    HTTPServer(('0.0.0.0', port), HealthCheckHandler).serve_forever()

def run_robot_loop():
    # 这里的顺序决定了执行顺序
    scripts = ["hao123.py", "hao456.py", "hao789.py", "hao888.py"]
    
    while True:
        for script in scripts:
            print(f"\n--- [🕒 {time.strftime('%X')}] 准备执行: {script} ---")
            
            try:
                # 重点优化：增加 timeout=300（5分钟），如果5分钟没跑完强制杀掉，跑下一个
                subprocess.run(["python", script], timeout=300) 
                print(f"--- [✅ {time.strftime('%X')}] {script} 正常结束 ---")
            except subprocess.TimeoutExpired:
                print(f"--- [⚠️ {time.strftime('%X')}] {script} 运行超时，已强制跳过 ---")
            except Exception as e:
                print(f"--- [❌ {time.strftime('%X')}] {script} 发生错误: {e} ---")
            
            # 每个脚本跑完后，雷打不动休息 15 分钟
            print(f"等待 30 分钟后切换到下一个脚本...")
            time.sleep(900)

if __name__ == "__main__":
    # [span_0](start_span)启动健康检查，防止 Render 关机[span_0](end_span)
    threading.Thread(target=run_server, daemon=True).start()
    # 启动顺序调度
    run_robot_loop()
