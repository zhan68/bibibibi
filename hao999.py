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
    """针对 pg.xxjiajia.com 的抓取逻辑"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    # 禁用图片以节省内存
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(45)
        print(">>> 正在访问 pg.xxjiajia.com...")
        driver.get("https://pg.xxjiajia.com") 
        
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "copy-pass-btn")))
        
        user_elements = driver.find_elements(By.CLASS_NAME, "card-text")
        pass_buttons = driver.find_elements(By.CLASS_NAME, "copy-pass-btn")
        
        account_data = []
        for i in range(min(len(user_elements), len(pass_buttons))):
            try:
                username = user_elements[i].text.strip()
                password = pass_buttons[i].get_attribute("data-clipboard-text")
                
                # --- 此处为修复后的缩进逻辑 ---
                if "@" in username and password:
                    res = (f"👤 账号：`{escape_markdown(username)}`\n"
                           f"🔑 密码：`{escape_markdown(password)}`")
                    account_data.append(res)
                # --------------------------
            except:
                continue
        
        print(f">>> 成功抓取到 {len(account_data)} 个账号")
        return account_data
    except Exception as e:
        print(f"❌ 抓取异常: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def send_to_telegram(content_list):
    """发送带加粗格式的消息"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not content_list: return

    header = f"🚀 *{escape_markdown('最新 Apple ID 共享更新')}*"
    body = "\n\n──────────────\n\n".join(content_list)
    
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    time_str = f"🕒 更新时间：{escape_markdown(bj_time)}"
    warning_str = f"⚠️ *{escape_markdown('警告：严禁在设置/iCloud中登录！')}*"
    
    # 广告加粗
    ad_text = (
        f"*共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，"
        f"请持续关注频道等待两个小时更新，请谅解*\n\n"
        f"*❤️ 欢迎关注我们频道：@yinlianID*\n"
        f"            *客    服：@zzyyy*"
    )
    
    full_caption = f"{header}\n\n{body}\n\n{time_str}\n{warning_str}\n\n──────────────\n\n{ad_text}"

    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    payload = {
        "chat_id": chat_id,
        "photo": img_url,
        "caption": full_caption,
        "parse_mode": "MarkdownV2"
    }
    
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            print(">>> 推送成功！已应用加粗格式。")
        else:
            print(f">>> 推送失败: {res.text}")
    except Exception as e:
        print(f">>> 请求异常: {e}")

if __name__ == "__main__":
    data = get_apple_ids()
    if data:
        send_to_telegram(data)
