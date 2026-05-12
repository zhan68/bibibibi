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
            
            success = False
            try:
                # 设定 5 分钟超时保护，防止单个脚本卡死
                # 使用 check=True 配合异常捕获
                subprocess.run(["python", script], timeout=300, check=True) 
                print(f"--- [✅ {time.strftime('%X')}] {script} 正常结束 ---")
                success = True
            except subprocess.TimeoutExpired:
                print(f"--- [⚠️ {time.strftime('%X')}] {script} 运行超时(5分钟)，已强制跳过 ---")
            except subprocess.CalledProcessError:
                print(f"--- [❌ {time.strftime('%X')}] {script} 脚本内部报错退出 ---")
            except Exception as e:
                print(f"--- [❌ {time.strftime('%X')}] {script} 系统异常: {e} ---")
            
            # --- 智能休息逻辑 ---
            if success:
                # 脚本成功运行，按原计划休息 15 分钟
                print(f">>> [System] 脚本运行成功，等待 15 分钟...")
                time.sleep(900)
            else:
                # 脚本失败（如 hao789 死机），仅休息 2 分钟便尝试下一个
                # 这样可以防止某一个源坏掉导致整个下午都没更新
                print(f">>> [⚠️ System] 脚本异常，为了保活，将在 2 分钟后切换下一个...")
                time.sleep(120)

if __name__ == "__main__":
    # 1. 在后台线程启动健康检查
    threading.Thread(target=run_server, daemon=True).start()
    
    # 2. 启动脚本顺序调度主循环
    print(">>> [System] 正在启动 Docker 自动化调度集群...")
    run_robot_loop()
