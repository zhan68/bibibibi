import os
import requests
import time
import re
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_apple_ids():
    chrome_options = Options()
    # --- Render 环境必须参数 ---
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    # 禁止加载图片以节省内存
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.binary_location = "/usr/bin/google-chrome" 

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        print("正在抓取数据...")
        driver.get("https://xdd.net.tr/share/wRjpcyhumY") # 记得每个文件修改对应的 URL
        wait = WebDriverWait(driver, 20)
        
        # 密码解锁逻辑
        pwd_input = wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
        pwd_input.send_keys("7778")
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button, .btn-primary")
        driver.execute_script("arguments[0].click();", submit_btn)
        
        time.sleep(8) # 等待数据加载
        
        user_btns = driver.find_elements(By.CLASS_NAME, "copy-btn")
        pass_btns = driver.find_elements(By.CLASS_NAME, "copy-pass-btn")
        
        account_data = []
        for i in range(min(len(user_btns), len(pass_btns))):
            username = user_btns[i].get_attribute("data-clipboard-text")
            password = pass_btns[i].get_attribute("data-clipboard-text")
            if username and password and "http" not in username:
                res = (f"👤 账号：`{escape_markdown(username)}`\n"
                       f"🔑 密码：`{escape_markdown(password)}`")
                account_data.append(res)
        
        return account_data

    except Exception as e:
        print(f"运行出错: {e}")
        return None
    finally:
        if driver:
            driver.quit() # 必须关闭，否则内存会爆

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not content_list: return

    body = "\n\n──────────────\n\n".join(content_list)
    bj_time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    
    header = "🚀 *最新 Apple ID 共享更新【2】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n🕒 更新时间：{escape_markdown(bj_time)}"

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    payload = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    requests.post(url, json=payload)

if __name__ == "__main__":
    data = get_apple_ids()
    if data:
        send_to_telegram(data)
