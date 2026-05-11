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
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def send_error_to_tg(msg, photo_path=None):
    """抓取失败时，发送网页截图到频道排查原因"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not photo_path: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={'chat_id': chat_id, 'caption': f"❌ 源3(Moe)抓取失败报告\n{msg}"}, files={'photo': photo})
    except: pass

def get_apple_ids():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        driver.get("https://appleid.moe233.app/share/GURdOstilD")
        wait = WebDriverWait(driver, 30)
        
        # 等待按钮加载
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "copy-btn")))
        
        # 定位账号和密码按钮
        user_btns = driver.find_elements(By.CSS_SELECTOR, ".copy-btn")
        pass_btns = driver.find_elements(By.CSS_SELECTOR, ".copy-pass-btn")
        
        account_data = []
        for i in range(min(len(user_btns), len(pass_btns))):
            # 提取 data-clipboard-text 属性
            username = user_btns[i].get_attribute("data-clipboard-text") or user_btns[i].text.strip()
            password = pass_btns[i].get_attribute("data-clipboard-text") or pass_btns[i].text.strip()
            
            # 过滤掉非邮箱账号（如网址或空值）
            if "http" in username.lower() or "@" not in username:
                continue
                
            if username and password:
                res = (f"📍 地区：{escape_markdown('共享账号')}\n"
                       f"👤 账号：`{escape_markdown(username)}`\n"
                       f"🔑 密码：`{escape_markdown(password)}`")
                account_data.append(res)
        
        driver.quit()
        return account_data
    except Exception as e:
        scr_path = "error_moe.png"
        driver.save_screenshot(scr_path)
        send_error_to_tg(f"源3抓取异常: {str(e)[:100]}", scr_path)
        driver.quit()
        return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not content_list: return

    body = "\n\n──────────────\n\n".join(content_list)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    notice = (
        f"🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"⚠️ *警告：严禁在设置/iCloud中登录！*\n\n"
        f"*共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待两个小时更新，请谅解*\n\n"
        f"❤️ *欢迎关注我们频道：*@{escape_markdown('yinlianID')}\n"
        f"            *客    服：*@{escape_markdown('zzyyy')}"
    )
    
    header = "🚀 *最新 Apple ID 共享更新【3】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    # 强制图片置顶逻辑
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    data = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    
    if len(full_caption) > 1020:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    requests.post(url, json=data)

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
