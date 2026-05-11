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
    [span_0](start_span)"""转义 Telegram MarkdownV2 特殊字符[span_0](end_span)"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def start_browser():
    [span_1](start_span)[span_2](start_span)"""配置适用于 Render Docker 环境的浏览器[span_1](end_span)[span_2](end_span)"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    # [span_3](start_span)显式指定 Render 中的 Chrome 路径[span_3](end_span)
    chrome_options.binary_location = "/usr/bin/google-chrome" 
    # 内存优化：禁止加载图片
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def get_apple_ids():
    [span_4](start_span)"""获取并解析 Apple ID[span_4](end_span)"""
    driver = None
    try:
        driver = start_browser()
        driver.get("https://idfree.top/") 
        wait = WebDriverWait(driver, 30)
        
        # 1. 点击确认按钮解除限制
        try:
            confirm_btn = wait.until(EC.element_to_be_clickable((By.ID, "confirmProceed")))
            driver.execute_script("arguments[0].click();", confirm_btn)
        except Exception as e:
            print(f"确认按钮跳过或异常: {e}")

        # 2. 等待渲染
        time.sleep(10) 
        
        # 3. 解析账号
        accounts = driver.find_elements(By.CSS_SELECTOR, "#accountList > div")
        account_data = []
        
        for acc in accounts:
            inputs = acc.find_elements(By.TAG_NAME, "input")
            if len(inputs) >= 2:
                username = inputs[0].get_attribute("value")
                password = inputs[1].get_attribute("value")
                if username and password and "@" in username:
                    res = (f"👤 账号：`{escape_markdown(username)}`\n"
                           f"🔑 密码：`{escape_markdown(password)}`")
                    account_data.append(res)
        
        return account_data
    except Exception as e:
        print(f"抓取异常: {e}")
        return None
    finally:
        if driver:
            [span_5](start_span)driver.quit() # 核心：强制退出浏览器释放内存[span_5](end_span)

def send_to_telegram(content_list):
    [span_6](start_span)"""发送更新到 Telegram，包含图片置顶逻辑[span_6](end_span)"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not content_list: return

    # 组装消息
    body = "\n\n──────────────\n\n".join(content_list)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    header = "🚀 *最新 Apple ID 共享更新【1】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    notice = f"🕒 更新时间：{escape_markdown(bj_time)}\n⚠️ *严禁在设置/iCloud中登录！*"
    
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    # 1024字符检查
    if len(full_caption) <= 1024:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        data = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    else:
        # 超长则发送文字，预览图置顶
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    res = requests.post(url, json=data)
    print(f"推送结果: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
