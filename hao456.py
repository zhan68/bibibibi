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

def get_apple_ids():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 模拟真实移动端 User-Agent，降低被封概率
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        print("开始访问页面...")
        driver.get("https://xdd.net.tr/share/wRjpcyhumY")
        wait = WebDriverWait(driver, 30)
        
        # --- 1. 强力密码解锁逻辑 ---
        try:
            print("正在寻找密码输入框...")
            # 扩大搜索范围，寻找页面上任何 input
            pwd_input = wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
            pwd_input.clear()
            pwd_input.send_keys("7778")
            
            # 寻找提交按钮
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button, .btn-primary, input[type='submit']")
            driver.execute_script("arguments[0].click();", submit_btn)
            print("密码已提交，等待页面跳转...")
            time.sleep(12) # 增加等待时长
        except Exception as e:
            print(f"密码环节处理异常: {e}")

        # --- 2. 账号解析与过滤逻辑 ---
        print("正在解析账号数据...")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "copy-btn")))
        
        user_btns = driver.find_elements(By.CLASS_NAME, "copy-btn")
        pass_btns = driver.find_elements(By.CLASS_NAME, "copy-pass-btn")
        
        account_data = []
        for i in range(min(len(user_btns), len(pass_btns))):
            username = user_btns[i].get_attribute("data-clipboard-text") or user_btns[i].text.strip()
            password = pass_btns[i].get_attribute("data-clipboard-text") or pass_btns[i].text.strip()
            
            # 核心过滤：剔除包含网址的无效项
            if "http" in username.lower() or "/" in username:
                continue
                
            if username and password:
                res = (f"👤 账号：`{escape_markdown(username)}`\n"
                       f"🔑 密码：`{escape_markdown(password)}`")
                account_data.append(res)
        
        driver.quit()
        return account_data

    except Exception as e:
        print(f"抓取过程崩溃: {e}")
        # 失败时保存截图并发送给 TG 进行远程调试
        screenshot_path = "error_debug.png"
        driver.save_screenshot(screenshot_path)
        send_error_to_tg(f"抓取崩溃日志: {e}", screenshot_path)
        driver.quit()
        return None

def send_error_to_tg(msg, photo_path=None):
    """当抓取失败时，发送截图到 Telegram 方便排查"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not token: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        requests.post(url, data={'chat_id': chat_id, 'caption': f"❌ 脚本运行失败报告\n{msg}"}, files={'photo': photo})

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not content_list: return

    # 1. 组装消息
    body = "\n\n──────────────\n\n".join(content_list)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    notice = (
        f"🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"⚠️ *警告：严禁在设置/iCloud中登录！*\n\n"
        f"*共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待15分钟更新，请谅解*\n\n"
        f"❤️ *欢迎关注我们频道：*@{escape_markdown('yinlianID')}\n"
        f"          *客    服：*@{escape_markdown('zzyyy')}"
    )
    
    header = "🚀 *最新 Apple ID 共享更新【2】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    # 2. 发送逻辑：优先图片模式，超长则切换文字模式
    if len(full_caption) < 1020:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    requests.post(url, json=payload)

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
