import os
import requests
import time
import re
import json
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def escape_markdown(text):
    """转义 Telegram MarkdownV2 特殊字符"""
    escape_chars = r'_[]()~>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_apple_ids():
    """获取并解析新网站的 Apple ID"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://proxy4all.github.io/FreeShadowrocket/") 
        wait = WebDriverWait(driver, 30)
        
        # 等待页面加载
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "body")))
        time.sleep(5) 
        
        # 获取网页上所有的文本行
        page_text = driver.find_element(By.TAG_NAME, "body").text
        driver.quit()
        
        lines = [line.strip() for line in page_text.split('\n') if line.strip()]
        account_data = []
        
        # 精准顺序状态机匹配
        for i in range(len(lines)):
            current_line = lines[i]
            
            # 1. 检查当前行是否包含邮箱（即账号）
            if "@" in current_line and ("账号" in current_line or "ID" in current_line or "mail" in current_line.lower()):
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', current_line)
                if email_match:
                    username = email_match.group(0)
                    password = None
                    
                    # 2. 从当前行往下寻找最近的密码行（通常在紧接着的 1-2 行内）
                    for j in range(i + 1, min(i + 3, len(lines))):
                        next_line = lines[j]
                        if "密码" in next_line or "pwd" in next_line.lower() or "password" in next_line.lower():
                            # 提取冒号或分割符后面的密码内容
                            pass_parts = re.split(r'：|:|\s+', next_line)
                            if len(pass_parts) > 1:
                                # 过滤掉标签名，拿到纯密码
                                password = next_line.replace(pass_parts[0], "").timezone = "".join(re.split(r'^[^a-zA-Z0-9]+', next_line.split(pass_parts[0])[-1])).strip()
                                # 如果过滤后太杂，直接取最后一部分
                                if not password:
                                    password = pass_parts[-1].strip()
                            break
                    
                    # 3. 如果成功配对，生成符合你频道视觉效果的格式
                    if username and password:
                        res = (f"📍 地区：{escape_markdown('共享账号')}\n"
                               f"👤 账号：\n`{escape_markdown(username)}`\n"
                               f"🔑 密码：`{escape_markdown(password)}`")
                        if res not in account_data:
                            account_data.append(res)
                            
        return account_data
        
    except Exception as e:
        print(f"抓取异常: {str(e)}")
        return None

def send_to_telegram_fixed(content_list):
    """发送带格式的消息（带置顶图片和文本加粗）"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    
    if not content_list:
        print("没有读取到有效ID账号，停止推送。")
        return

    # 打印出来在日志里让你看一眼抓到的结果
    print(f"成功抓取到 {len(content_list)} 个账号，准备推送...")

    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    header = f"🚀 *{escape_markdown('最新 Apple ID 共享更新【4】')}*"
    body = "\n\n" + "\n\n──────────────\n\n".join(content_list)
    
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    time_str = f"🕒 更新时间：{escape_markdown(bj_time)}"
    
    warning_str = f"⚠️ *{escape_markdown('警告：严禁在设置/iCloud中登录！')}*"
    
    notice_val = "共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待两个小时更新，请谅解"
    notice_str = f"*{escape_markdown(notice_val)}*"
    
    follow_str = f"❤️ *{escape_markdown('欢迎关注我们频道：')}*@yinlianID"
    service_str = f"            *{escape_markdown('客    服：')}*@zzyyy"
    
    caption = (
        f"{header}\n{body}\n\n"
        f"{time_str}\n"
        f"{warning_str}\n\n"
        f"{notice_str}\n\n"
        f"{follow_str}\n"
        f"{service_str}"
    )
    
    if len(caption) > 1024:
        if len(content_list) > 2:
            body = "\n\n" + "\n\n──────────────\n\n".join(content_list[:2])
            caption = f"{header}\n{body}\n\n{time_str}\n{warning_str}\n\n{notice_str}\n\n{follow_str}\n{service_str}"

    media_group = [
        {
            'type': 'photo',
            'media': img_url,
            'caption': caption,
            'parse_mode': 'MarkdownV2'
        }
    ]

    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    payload = {
        "chat_id": chat_id,
        "media": json.dumps(media_group)
    }
    
    res = requests.post(url, data=payload)
    if res.status_code == 200:
        print("推送成功！")
    else:
        print(f"推送失败: {res.text}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram_fixed(data)
