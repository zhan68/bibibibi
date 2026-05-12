import os
import requests
import time
import re
import signal  # 引入信号模块
from datetime import datetime, timedelta, timezone
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# 设置脚本最大运行时间（秒），防止卡死导致调度器不切换
def handler(signum, frame):
    raise Exception("脚本运行超时，已强制退出")

signal.signal(signal.SIGALRM, handler)
signal.alarm(300)  # 5分钟强制结束

def escape_markdown(text):
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def start_browser():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.binary_location = "/usr/bin/google-chrome" 
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    # 设置页面加载超时
    driver.set_page_load_timeout(60) 
    return driver

def get_apple_ids():
    driver = None
    try:
        driver = start_browser()
        print(">>> [hao123] 正在访问 idfree.top...")
        driver.get("https://idfree.top/") 
        wait = WebDriverWait(driver, 30)
        
        try:
            confirm_btn = wait.until(EC.element_to_be_clickable((By.ID, "confirmProceed")))
            driver.execute_script("arguments[0].click();", confirm_btn)
        except:
            pass

        time.sleep(8) 
        
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
        
        print(f">>> [hao123] 成功解析出 {len(account_data)} 个账号")
        return account_data
    except Exception as e:
        print(f">>> [hao123] 抓取异常: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not content_list: return

    body = "\n\n──────────────\n\n".join(content_list)
    bj_time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    
    header = "🚀 *最新 Apple ID 共享更新【1】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
        notice = (
        f"🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"⚠️ *严禁在设置/iCloud中登录！*\n\n"
        f"共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待两个小时更新，请谅解\n\n"
        f"❤️ *欢迎关注我们频道：*@{escape_markdown('yinlianID')}\n"
        f"          *客    服：*@{escape_markdown('zzyyy')}"
    )

    if len(full_caption) <= 1024:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        data = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    res = requests.post(url, json=data)
    print(f">>> [hao123] 推送状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    if data:
        send_to_telegram(data)
    print(">>> [hao123] 脚本执行完毕，退出进程。")
