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

def escape_markdown(text):
    """转义 Telegram MarkdownV2 特殊字符"""
    escape_chars = r'_[]()~>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_apple_ids():
    """获取并解析 Apple ID"""
    chrome_options = Options()
    
    # 💡 核心自愈补丁：锁定 Docker 容器内部官方 Chrome 路径，彻底干掉 DriverManager
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument('--headless=new')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        print("🚀 [通道 1] 正在直接调动系统原生 Chrome 驱动开跑...")
        driver = webdriver.Chrome(options=chrome_options)
        driver.get("https://idfree.top/") 
        wait = WebDriverWait(driver, 30)
        
        try:
            confirm_btn = wait.until(EC.element_to_be_clickable((By.ID, "confirmProceed")))
            driver.execute_script("arguments[0].click();", confirm_btn)
        except Exception:
            pass

        time.sleep(8) 
        
        accounts = driver.find_elements(By.CSS_SELECTOR, "#accountList > div")
        account_data = []
        
        for acc in accounts:
            try:
                inputs = acc.find_elements(By.TAG_NAME, "input")
                if len(inputs) >= 2:
                    username = inputs[0].get_attribute("value")
                    password = inputs[1].get_attribute("value")
                    
                    if username and password:
                        res = (f"👤 账号：`{escape_markdown(username)}`\n"
                               f"🔑 密码：`{escape_markdown(password)}`")
                        account_data.append(res)
            except:
                continue
        
        driver.quit()
        return account_data
    except Exception as e:
        print(f"❌ [通道 1] 抓取异常: {str(e)}")
        try: driver.quit()
        except: pass
        return None

def send_to_telegram_fixed(content_list):
    """发送带格式的消息"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    
    if not content_list:
        print("⚠️ [通道 1] 未获取到有效数据，取消本次 TG 推送。")
        return

    print(f"🎉 [通道 1] 成功抓取到 {len(content_list)} 组账号，正在向 TG 推送最新大帖...")
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    header = f"🚀 *{escape_markdown('最新 Apple ID 共享更新【1】')}*"
    body = "\n\n" + "\n\n──────────────\n\n".join(content_list)
    
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    time_str = f"🕒 更新时间：{escape_markdown(bj_time)}"
    warning_str = f"⚠️ *{escape_markdown('警告：严禁在设置/iCloud中登录！')}*"
    
    notice_val = "共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待15分钟更新，请谅解"
    notice_str = f"*{escape_markdown(notice_val)}*"
    
    follow_str = f"❤️ *{escape_markdown('欢迎关注我们交流群：')}*@bh888"
    service_str = f"            *{escape_markdown('客    服：')}*@zzyyy"
    
    caption = f"{header}\n{body}\n\n{time_str}\n{warning_str}\n\n{notice_str}\n\n{follow_str}\n{service_str}"
    
    media_group = [{'type': 'photo', 'media': img_url, 'caption': caption, 'parse_mode': 'MarkdownV2'}]
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    
    res = requests.post(url, data={"chat_id": chat_id, "media": json.dumps(media_group)})
    if res.status_code == 200:
        print("🎉 [通道 1] 大图大贴推送成功！")
    else:
        print(f"❌ [通道 1] 推送失败: {res.text}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram_fixed(data)
