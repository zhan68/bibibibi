import subprocess
import time
import os
import threading
import sys
import re
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer

def escape_markdown_v2(text):
    """高级转义函数：精准转义 Telegram MarkdownV2 特殊字符，绝不污染加粗和代码块语法"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def send_no_id_notice_to_tg(script_name):
    """当任意通道没有抓取到可用ID时，由主大脑统一向频道推送极其干净优雅的纯文字通知"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not token:
        print(f"⚠️ [System] 未检测到环境变量 BOT_TOKEN，放弃发送无号通知。")
        return
        
    name_map = {
        "hao123.py": "【通道 1】",
        "hao456.py": "【通道 2】",
        "hao789.py": "【通道 3】",
        "hao888.py": "【通道 4】",
        "hao999.py": "【通道 5】",
        "hao666.py": "【通道 6】"
    }
    
    channel_display_name = name_map.get(script_name, f"【{script_name}】")
    bj_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + 28800))
    
    header = "🚀 *最新 Apple ID 共享更新提示*"
    status_str = "📍 状态：🔴 *当前暂无可用的活号*"
    body = f"📋 *通知提醒：*\n经系统实时动态监测，当前 *{escape_markdown_v2(channel_display_name)}* 目标网站线上正处于维护或账号锁定状态，本次轮询未嗅探到可用的有效活号。"
    hint_str = f"*{escape_markdown_v2('请大家稍安勿躁，请耐心等待下一轮自动轮询更新，或关注频道内其他正常通道，感谢理解！')}*"
    
    time_str = f"🕒 监测时间：{escape_markdown_v2(bj_time)}"
    follow_str = f"❤️ *{escape_markdown_v2('欢迎关注我们交流群：')}*@bh888"
    service_str = f"            *{escape_markdown_v2('客    服：')}*@zzyyy"
    
    full_text = f"{header}\n\n{status_str}\n\n{body}\n\n{hint_str}\n\n──────────────\n\n{time_str}\n{follow_str}\n{service_str}"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        res = requests.post(url, json={"chat_id": chat_id, "text": full_text, "parse_mode": "MarkdownV2"})
        if res.status_code == 200:
            print(f"📢 [System] 已向频道成功广播 {channel_display_name} 暂无可用 ID 通知")
        else:
            print(f"❌ [System] 广播无号通知失败，TG返回: {res.text}")
    except Exception as e:
        print(f"❌ [System] 发送无号通知请求崩溃: {e}")

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
    scripts = ["hao123.py", "hao456.py", "hao789.py", "hao888.py", "hao999.py", "hao666.py"]
    current_env = os.environ.copy()
    
    while True:
        for script in scripts:
            print(f"\n--- [🕒 {time.strftime('%X')}] 准备执行: {script} ---")
            has_live_ids = True # 默认放行大休眠依据
            
            try:
                # 实时管道对冲，防止容器积压卡死
                result = subprocess.run(
                    [sys.executable, script], 
                    timeout=300, 
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True, 
                    env=current_env
                ) 
                
                output_str = result.stdout if result.stdout else ""
                print(output_str)

                if result.returncode == 0:
                    # 精准捕捉各通道打印出来的未捕获活号关键字
                    if any(k in output_str for k in ["未获取到有效数据", "没有读取到任何", "最终未捕获到", "取消本次 TG 推送", "最终提纯出的列表为空"]):
                        print(f"ℹ️ [System] 后台日志捕获成功：{script} 线上无可用活号。")
                        send_no_id_notice_to_tg(script)
                        has_live_ids = False  
                    else:
                        print(f"🎉 [System] {script} 顺利抓取到活号并已成功发布大贴！")
                        has_live_ids = True   
                    print(f"--- [✅] {script} 正常结束 ---")
                else:
                    print(f"--- [❌] {script} 进程异常退出，状态码: {result.returncode}，触发无号通报兜底...")
                    send_no_id_notice_to_tg(script)
                    has_live_ids = False
                    
            except Exception as e:
                print(f"--- [❌] {script} 运行突发崩溃: {e}，触发无号通报兜底... ---")
                send_no_id_notice_to_tg(script)
                has_live_ids = False
            
            # 严格按照铁律休眠：发大贴睡15分钟，无号快闪避2分钟
            wait_time = 900 if has_live_ids else 120
            print(f">>> [System] 单通道排队隔离清算：{script} 执行完毕，强制原地休眠 {wait_time} 秒...")
            time.sleep(wait_time)

if __name__ == "__main__":
    threading.Thread(target=run_server, daemon=True).start()
    run_robot_loop()
