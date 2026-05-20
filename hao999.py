import os
import requests
import time
import re
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def escape_markdown(text):
    """转义 Telegram MarkdownV2 特殊字符"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_apple_ids():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        driver.get(target_url)
        
        # 稳妥起见，给予 10 秒充足时间让加密的文档文本解密并渲染完毕
        print("等待网页底层数据渲染 (10秒)...")
        time.sleep(10)
        
        # 【核心改动】：不拿 body.text（防止混乱缩进），直接拿最原始的 HTML 源码
        html_content = driver.page_source
        driver.quit()
        
        print("网页源码提取成功，开始强力清洗数据...")
        
        # 1. 把 HTML 里的标签、脚本全部洗掉，转换为干净的、保留换行符的纯文本
        # 这能确保不管前端怎么变，账号、密码、状态的相对行数和相对距离是绝对固定的
        clean_text = re.sub(r'<script.*?</script>', '', html_content, flags=re.DOTALL)
        clean_text = re.sub(r'<style.*?</style>', '', clean_text, flags=re.DOTALL)
        clean_text = re.sub(r'<[^>]+>', '\n', clean_text)  # 把所有 HTML 标签变成换行符
        
        # 2. 规整文本，去除多余空行
        lines = [line.strip() for line in clean_text.split('\n') if line.strip()]
        print(f"规整后有效文本共 {len(lines)} 行")
        
        account_data = []
        
        # 3. 遍历每一行寻找邮箱账号
        for i, line in enumerate(lines):
            # 匹配标准的邮箱格式作为 Apple ID 账号
            if re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', line):
                username = line
                password = ""
                status_ok = False
                
                # 4. 在当前账号往后看 5 行范围内，寻找与之匹配的密码和状态
                look_ahead = lines[i+1 : min(i+6, len(lines))]
                
                # 检查后 5 行内是否有“状态正常”或“正常”
                for context_line in look_ahead:
                    if "正常" in context_line or "状态正常" in context_line:
                        status_ok = True
                    
                    # 寻找长得像密码的行：长度在 6 到 22 位，不能是状态词，不包含特殊汉字
                    if (6 <= len(context_line) <= 22) and not any(x in context_line for x in ["正常", "锁定", "更新", "检测", "@", "http"]):
                        # 排除掉类似于“密码”两个字的引导词
                        if not re.search(r'[\u4e00-\u9fa5]', context_line):
                            password = context_line
                
                # 5. 如果“状态正常”通过，并且顺利拿到了密码，则记录
                if status_ok and password:
                    res = (f"📍 地区：{escape_markdown('源2-共享')}\n"
                           f"👤 账号：`{escape_markdown(username)}`\n"
                           f"🔑 密码：`{escape_markdown(password)}`")
                    
                    if res not in account_data:
                        account_data.append(res)
                        print(f"🚩 成功捕获正常账号: {username}")
                elif not status_ok:
                    print(f"⚠️ 账号 {username} 被过滤（原因：状态非正常）")
                    
        return account_data

    except Exception as e:
        print(f"抓取过程崩溃: {e}")
        driver.quit()
        return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not content_list: 
        print("没有获取到有效账号，取消发送。")
        return

    body = "\n\n──────────────\n\n".join(content_list)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    notice = (
        f"🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"⚠️ *警告：严禁在设置/iCloud中登录！*\n\n"
        f"*共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待两个小时更新，请谅解*\n\n"
        f"❤️ *欢迎关注我们频道：*@{escape_markdown('yinlianID')}\n"
        f"          *客    服：*@{escape_markdown('zzyyy')}"
    )
    
    header = "🍎 *最新 Apple ID 共享更新（5）*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    if len(full_caption) < 1020:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    res = requests.post(url, json=payload)
    print(f"TG 发送状态: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
