import subprocess
import time
import os
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# --- 健康检查服务器配置 ---
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Cluster Active")

def run_server():
    # 获取 Render 端口，默认为 10000
    port = int(os.environ.get("PORT", 10000))
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    print(f">>> [System] 健康检查服务器已启动，监听端口: {port}")
    server.serve_forever()

# --- 脚本调度循环 ---
def run_robot_loop():
    # 定义需要轮流执行的脚本列表
    scripts = ["hao123.py", "hao456.py", "hao789.py", "hao888.py"]
    
    while True:
        for script in scripts:
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            print(f"\n--- [🕒 {current_time}] 准备执行: {script} ---")
            
            try:
                # 设定 5 分钟超时保护，防止单个脚本卡死导致整个流程停止
                subprocess.run(["python", script], timeout=300) 
                print(f"--- [✅ {time.strftime('%X')}] {script} 正常结束 ---")
            except subprocess.TimeoutExpired:
                print(f"--- [⚠️ {time.strftime('%X')}] {script} 运行超时，已强制跳过 ---")
            except Exception as e:
                print(f"--- [❌ {time.strftime('%X')}] {script} 发生错误: {e} ---")
            
            # 每个脚本跑完后，休息 15 分钟 (900秒)
            # 一轮跑完（4个脚本）总计耗时约 65-70 分钟
            print(f">>> [System] 等待 15 分钟后切换到下一个脚本...")
            time.sleep(900)

if __name__ == "__main__":
    # 1. 在后台线程启动健康检查，防止 Render 因无 Web 请求而关机
    threading.Thread(target=run_server, daemon=True).start()
    
    # 2. 启动脚本顺序调度主循环
    run_robot_loop()
