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
    """转义 Telegram MarkdownV2 特殊字符，注意不能转义我们要用的格式符号如 * 和 ` """
    # 这里的转义去掉了 * 和 `，因为我们要手动控制它们
    escape_chars = r'_[]()~>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_apple_ids():
    """获取并解析 Apple ID"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://pg.xxjiajia.com") 
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
                        # 账号信息排版
                        res = (f"📍 地区：{escape_markdown('共享账号')}\n"
                               f"👤 账号：\n`{escape_markdown(username)}`\n"
                               f"🔑 密码：`{escape_markdown(password)}`")
                        account_data.append(res)
            except:
                continue
        
        driver.quit()
        return account_data
    except Exception as e:
        print(f"抓取异常: {str(e)}")
        return None

def send_to_telegram_fixed(content_list):
    """发送带格式的消息"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    
    if not content_list:
        print("未获取到有效数据")
        return

    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    # --- 核心修改：严格遵循 MarkdownV2 加粗语法 ---
    
    # 1. 标题加粗
    header = f"🚀 *{escape_markdown('最新 Apple ID 共享更新【5】')}*"
    
    # 2. 账号主体
    body = "\n\n" + "\n\n──────────────\n\n".join(content_list)
    
    # 3. 时间与警告
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    time_str = f"🕒 更新时间：{escape_markdown(bj_time)}"
    # 警告整行加粗
    warning_str = f"⚠️ *{escape_markdown('警告：严禁在设置/iCloud中登录！')}*"
    
    # 4. 公告内容（整段加粗）
    notice_val = "共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待两个小时更新，请谅解"
    notice_str = f"*{escape_markdown(notice_val)}*"
    
    # 5. 底部客服信息（标签部分加粗）
    follow_str = f"❤️ *{escape_markdown('欢迎关注我们频道：')}*@yinlianID"
    service_str = f"            *{escape_markdown('客    服：')}*@zzyyy"
    
    # 组合最终 Caption
    caption = (
        f"{header}\n{body}\n\n"
        f"{time_str}\n"
        f"{warning_str}\n\n"
        f"{notice_str}\n\n"
        f"{follow_str}\n"
        f"{service_str}"
    )
    
    media_group = [
        {
            'type': 'photo',
            'media': img_url,
            'caption': caption,
            'parse_mode': 'MarkdownV2'
        }
    ]

    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    payload = {
        "chat_id": chat_id,
        "media": json.dumps(media_group)
    }
    
    res = requests.post(url, data=payload)

    if res.status_code == 200:
        print("推送成功！已应用加粗格式。")
    else:
        print(f"推送失败: {res.text}")
        # 如果还是报错，说明某些特殊字符没处理好，打印出来排查
        print(f"发送的内容是: {caption}")

if __name__ == "__main__":
    # 注意：确保环境变量 BOT_TOKEN 已设置
    data = get_apple_ids()
    send_to_telegram_fixed(data)
