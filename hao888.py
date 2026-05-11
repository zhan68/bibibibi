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
    """转义 Telegram MarkdownV2 特殊字符"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def start_browser():
    """配置适用于 Render Docker 环境的浏览器"""
    chrome_options = Options()
    # --- 必须参数 ---
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    
    # --- 显式指定 Render 中的 Chrome 路径 ---
    chrome_options.binary_location = "/usr/bin/google-chrome" 
    
    # --- 内存优化：禁止加载图片 ---
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    
    # 模拟真实移动端 User-Agent
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def send_error_to_tg(msg, photo_path=None):
    """当抓取失败时发送截图"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not photo_path: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={'chat_id': chat_id, 'caption': f"❌ 源4抓取失败报告\n{msg}"}, files={'photo': photo})
    except Exception as e:
        print(f"发送错误报告失败: {e}")

def get_apple_ids():
    driver = None
    try:
        driver = start_browser()
        print("开始访问源4页面...")
        driver.get("https://aunlock.laomaos.com/share/UnDjXSBtqh")
        wait = WebDriverWait(driver, 30)
        
        # --- 1. 密码解锁逻辑 ---
        try:
            pwd_input = wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
            pwd_input.clear()
            pwd_input.send_keys("112233")
            
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button, .btn-primary, input[type='submit']")
            driver.execute_script("arguments[0].click();", submit_btn)
            time.sleep(10) # 等待渲染
        except Exception as e:
            print(f"密码环节异常: {e}")

        # --- 2. 账号解析 ---
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "copy-btn")))
        user_btns = driver.find_elements(By.CLASS_NAME, "copy-btn")
        pass_btns = driver.find_elements(By.CLASS_NAME, "copy-pass-btn")
        
        account_data = []
        for i in range(min(len(user_btns), len(pass_btns))):
            username = user_btns[i].get_attribute("data-clipboard-text") or user_btns[i].text.strip()
            password = pass_btns[i].get_attribute("data-clipboard-text") or pass_btns[i].text.strip()
            
            # 过滤逻辑
            if "http" in username.lower() or "/" in username or "@" not in username:
                continue
                
            if username and password:
                res = (f"👤 账号：`{escape_markdown(username)}`\n"
                       f"🔑 密码：`{escape_markdown(password)}`")
                account_data.append(res)
        
        return account_data

    except Exception as e:
        print(f"源4抓取过程崩溃: {e}")
        if driver:
            screenshot_path = "error_source4.png"
            driver.save_screenshot(screenshot_path)
            send_error_to_tg(f"源4崩溃日志: {str(e)[:100]}", screenshot_path)
        return None
    finally:
        if driver:
            driver.quit() # 释放内存，防止宿主机卡死

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not content_list: return

    body = "\n\n──────────────\n\n".join(content_list)
    bj_time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    
    header = "🚀 *最新 Apple ID 共享更新【4】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n🕒 更新时间：{escape_markdown(bj_time)}"

    if len(full_caption) <= 1024:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    requests.post(url, json=payload)

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
