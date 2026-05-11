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
    """统一配置浏览器，适配 Render Docker 环境"""
    chrome_options = Options()
    # --- 必须参数 ---
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    # --- 优化参数：显式指定 Chrome 路径 ---
    chrome_options.binary_location = "/usr/bin/google-chrome" 
    # --- 内存优化：禁止加载图片 ---
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    # 模拟移动端 UA
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def send_error_to_tg(msg, photo_path=None):
    """抓取失败时发送报告"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not photo_path: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={'chat_id': chat_id, 'caption': f"❌ 源3抓取失败报告\n{msg}"}, files={'photo': photo})
    except: pass

def get_apple_ids():
    driver = None
    try:
        driver = start_browser()
        # 你的源3目标地址
        driver.get("https://appleid.moe233.app/share/GURdOstilD")
        wait = WebDriverWait(driver, 30)
        
        # 等待按钮加载
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "copy-btn")))
        
        # 定位账号和密码按钮
        user_btns = driver.find_elements(By.CSS_SELECTOR, ".copy-btn")
        pass_btns = driver.find_elements(By.CSS_SELECTOR, ".copy-pass-btn")
        
        account_data = []
        for i in range(min(len(user_btns), len(pass_btns))):
            username = user_btns[i].get_attribute("data-clipboard-text") or user_btns[i].text.strip()
            password = pass_btns[i].get_attribute("data-clipboard-text") or pass_btns[i].text.strip()
            
            # 过滤无效账号
            if "http" in username.lower() or "@" not in username:
                continue
                
            if username and password:
                res = (f"👤 账号：`{escape_markdown(username)}`\n"
                       f"🔑 密码：`{escape_markdown(password)}`")
                account_data.append(res)
        
        return account_data
    except Exception as e:
        print(f"抓取异常: {e}")
        if driver:
            scr_path = "error_moe.png"
            driver.save_screenshot(scr_path)
            send_error_to_tg(f"源3抓取异常: {str(e)[:100]}", scr_path)
        return None
    finally:
        if driver:
            driver.quit() # --- 核心：无论如何都要关闭浏览器，释放内存 ---

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not content_list: 
        print("未抓取到有效账号，跳过发送。")
        return

    body = "\n\n──────────────\n\n".join(content_list)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    notice = (
        f"🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"⚠️ *警告：严禁在设置/iCloud中登录！*\n\n"
        f"❤️ *欢迎关注我们频道：*@{escape_markdown('yinlianID')}"
    )
    
    header = "🚀 *最新 Apple ID 共享更新【3】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    # 消息发送逻辑
    if len(full_caption) <= 1024:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        data = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    else:
        # 如果超长，使用文字模式发送，预览图通过隐形链接置顶
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    response = requests.post(url, json=data)
    print(f"发送结果: {response.status_code}, {response.text}")

if __name__ == "__main__":
    # 确保在主程序中运行
    data = get_apple_ids()
    send_to_telegram(data)
