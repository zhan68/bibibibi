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
        
    # 💡 自动映射脚本对应的通道大名称，让粉丝一目了然
    name_map = {
        "hao123.py": "【通道 1】",
        "hao456.py": "【通道 2】",
        "hao789.py": "【通道 3】",
        "hao888.py": "【通道 4】",
        "hao999.py": "【通道 5】"
    }
    channel_display_name = name_map.get(script_name, f"【{script_name}】")
    
    # 获取精准的当前北京时间
    bj_time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime(time.time() + 28800))
    
    # 💡 严格遵循频道加粗与排版美化文本
    header = "🚀 *最新 Apple ID 共享更新提示*"
    status_str = "📍 状态：🔴 *当前暂无可用的活号*"
    body = f"📋 *通知提醒：*\n经系统实时动态监测，当前 *{escape_markdown_v2(channel_display_name)}* 目标网站线上正处于维护或账号锁定状态，本次轮询未嗅探到可用的有效活号。"
    hint_str = f"*{escape_markdown_v2('请大家稍安勿躁，请耐心等待下一轮自动轮询更新，或关注频道内其他正常通道，感谢理解！')}*"
    
    time_str = f"🕒 监测时间：{escape_markdown_v2(bj_time)}"
    follow_str = f"❤️ *{escape_markdown_v2('欢迎关注我们交流群：')}*@bh888"
    service_str = f"            *{escape_markdown_v2('客    服：')}*@zzyyy"
    
    # 完美用分割线拼接最终发送文本
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
    # 严格锁定的 5 大核心收割通道队列
    scripts = ["hao123.py", "hao456.py", "hao789.py", "hao888.py", "hao999.py"]
    current_env = os.environ.copy()
    
    while True:
        for script in scripts:
            print(f"\n--- [🕒 {time.strftime('%X')}] 准备执行: {script} ---")
            has_live_ids = False
            
            try:
                # 执行通道脚本并强行拦截它的控制台日志输出
                result = subprocess.run(
                    [sys.executable, script], 
                    timeout=300, 
                    capture_output=True, 
                    text=True, 
                    env=current_env
                ) 
                
                # 将子脚本的原本打印无缝平铺到 Render 后台日志中
                if result.stdout: print(result.stdout)
                if result.stderr: print(result.stderr)

                if result.returncode == 0:
                    # 💡 精准拦截无可用ID的退出信号
                    if any(k in result.stdout for k in ["未获取到有效数据", "没有读取到任何", "最终未捕获到", "取消本次 TG 推送"]):
                        print(f"ℹ️ [System] {script} 判定无活号，准备触发统一无号提醒...")
                        send_no_id_notice_to_tg(script)
                        has_live_ids = False  # 没抓到有效活号
                    else:
                        print(f"🎉 [System] {script} 顺利抓取到活号并已由子脚本成功发布大贴！")
                        has_live_ids = True   # 成功发出了活号大贴
                    print(f"--- [✅] {script} 正常结束 ---")
                else:
                    print(f"--- [❌] {script} 进程异常退出，状态码: {result.returncode}，触发无号通报兜底...")
                    send_no_id_notice_to_tg(script)
                    has_live_ids = False
                    
            except Exception as e:
                print(f"--- [❌] {script} 运行突发崩溃: {e}，触发无号通报兜底... ---")
                send_no_id_notice_to_tg(script)
                has_live_ids = False
            
            # 💡 【严格坚守铁律机制】
            # 如果成功发布了全加粗活号大贴，雷打不动在原地休眠 15 分钟（900秒），给粉丝腾出空档抢号！
            # 如果目标网站全锁或风控没抓到，为了让系统不卡死并高频切入下一个通道碰运气，仅快速休眠 2 分钟（120秒）闪避风控！
            wait_time = 900 if has_live_ids else 120
            print(f">>> [System] 单通道排队隔离清算：{script} 执行完毕，强制原地休眠 {wait_time} 秒...")
            time.sleep(wait_time)

if __name__ == "__main__":
    # 异步拉起健康检查防休眠服务器
    threading.Thread(target=run_server, daemon=True).start()
    run_robot_loop()
