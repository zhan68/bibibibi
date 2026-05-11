import subprocess
import time
import os

def run_script(name):
    print(f"[{time.strftime('%X')}] 正在运行: {name}...")
    try:
        # 运行指定的 python 文件
        subprocess.run(["python", name], check=True)
        print(f"[{time.strftime('%X')}] {name} 运行成功。")
    except Exception as e:
        print(f"[{time.strftime('%X')}] {name} 出错: {e}")

if __name__ == "__main__":
    # 定义需要轮流运行的文件列表
    scripts = ["hao123.py", "hao456.py", "hao789.py", "hao888.py"]
    
    while True:
        for script in scripts:
            run_script(script)
            # 每个文件运行完后，等待 15 分钟（900 秒）
            print(f"等待 15 分钟后运行下一个...")
            time.sleep(900) 
