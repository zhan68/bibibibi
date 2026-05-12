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
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(45)
        print(">>> 正在访问 pg.xxjiajia.com...")
        driver.get("https://pg.xxjiajia.com") 
        
        # 等待页面加载，特别是密码按钮出现
        wait = WebDriverWait(driver, 20)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "copy-pass-btn")))
        
        # 获取所有账号文本（card-text）和密码按钮（copy-pass-btn）
        user_elements = driver.find_elements(By.CLASS_NAME, "card-text")
        pass_buttons = driver.find_elements(By.CLASS_NAME, "copy-pass-btn")
        
        account_data = []
        # 遍历解析数据
        for i in range(min(len(user_elements), len(pass_buttons))):
            try:
                username = user_elements[i].text.strip()
                # 密码通常存储在按钮的 data-clipboard-text 属性中
                password = pass_buttons[i].get_attribute("data-clipboard-text")
                
                if "@" in username and password:
                    res = (f"👤 账号：`{escape_markdown(username)}`\n"
                           f"🔑 密码：`{escape_markdown(password)}`")
                    account_data.append(res)
            except:
                continue
        
        print(f">>> 成功解析出 {len(account_data)} 个账号")
        driver.quit()
        return account_data
    except Exception as e:
        print(f"❌ 抓取异常: {str(e)}")
        if 'driver' in locals(): driver.quit()
        return None

def send_to_telegram_fixed(content_list):
    """发送带加粗格式的消息"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not content_list: return

    # 1. 标题加粗
    header = f"🚀 *{escape_markdown('最新 Apple ID 共享更新【5】')}*"
    
    # 2. 账号主体
    body = "\n\n──────────────\n\n".join(content_list)
    
    # 3. 时间与警告
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    time_str = f"🕒 更新时间：{escape_markdown(bj_time)}"
    warning_str = f"⚠️ *{escape_markdown('警告：严禁在设置/iCloud中登录！')}*"
    
    # 4. 底部广告与客服（全加粗处理）
    ad_text = (
        f"*共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，"
        f"请持续关注频道等待两个小时更新，请谅解*\n\n"
        f"*❤️ 欢迎关注我们频道：@yinlianID*\n"
        f"            *客    服：@zzyyy*"
    )
    
    # 组合最终 Caption
    full_caption = (
        f"{header}\n\n"
        f"{body}\n\n"
        f"{time_str}\n"
        f"{warning_str}\n\n"
        f"──────────────\n\n"
        f"{ad_text}"
    )

    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    
    # 准备 payload，确保使用 MarkdownV2
    payload = {
        "chat_id": chat_id,
        "photo": img_url,
        "caption": full_caption,
        "parse_mode": "MarkdownV2"
    }
    
    # 使用 json=payload 确保数据格式正确
    res = requests.post(url, json=payload, timeout=20)

    if res.status_code == 200:
        print(">>> 推送成功！已应用加粗广告文案。")
    else:
        print(f">>> 推送失败: {res.text}")

if __name__ == "__main__":
    print("--- 启动 hao123.py 任务 ---")
    data = get_apple_ids()
    if data:
        send_to_telegram_fixed(data)
    print("--- 任务结束 ---")
