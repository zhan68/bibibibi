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
    """全量抓取并智能匹配账号密码"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = None
    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.set_page_load_timeout(60)
        
        print(">>> 正在访问账号分发页面...")
        # 直接穿透 iframe 访问源地址以提高稳定性
        driver.get("https://aunlock.laomaos.com/share/AlRBxzPEIC")
        
        # 等待任意带有数据的按钮加载
        wait = WebDriverWait(driver, 30)
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "[data-clipboard-text]")))
        
        # 获取所有具备 data-clipboard-text 属性的元素
        elements = driver.find_elements(By.CSS_SELECTOR, "[data-clipboard-text]")
        raw_values = [el.get_attribute("data-clipboard-text").strip() for el in elements if el.get_attribute("data-clipboard-text")]
        
        account_data = []
        # 智能双步进逻辑：两两配对，并验证第一个是否为邮箱格式
        i = 0
        while i < len(raw_values) - 1:
            user = raw_values[i]
            pwd = raw_values[i+1]
            
            # 如果当前项是账号，则将其与下一项配对
            if "@" in user:
                res = (f"👤 账号：`{escape_markdown(user)}`\n"
                       f"🔑 密码：`{escape_markdown(pwd)}`")
                account_data.append(res)
                i += 2 # 跳过已配对的两个
            else:
                i += 1 # 如果不是账号，往后挪一位继续找
        
        print(f">>> 成功解析出 {len(account_data)} 组账号密码")
        return account_data
    except Exception as e:
        print(f"❌ 抓取异常: {e}")
        return None
    finally:
        if driver:
            driver.quit()

def send_to_telegram(content_list):
    """发送带加粗广告的消息"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not content_list: return

    # 1. 标题与正文
    header = f"🚀 *{escape_markdown('最新 Apple ID 共享更新【5】')}*"
    body = "\n\n──────────────\n\n".join(content_list)
    
    # 2. 时间与警告
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    time_str = f"🕒 更新时间：{escape_markdown(bj_time)}"
    warning_str = f"⚠️ *{escape_markdown('警告：严禁在设置/iCloud中登录！')}*"
    
    # 3. 全加粗广告文案
    ad_text = (
        f"*共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，"
        f"请持续关注频道等待两个小时更新，请谅解*\n\n"
        f"*❤️ 欢迎关注我们频道：@yinlianID*\n"
        f"            *客    服：@zzyyy*"
    )
    
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
    
    payload = {
        "chat_id": chat_id,
        "photo": img_url,
        "caption": full_caption,
        "parse_mode": "MarkdownV2"
    }
    
    try:
        res = requests.post(url, json=payload, timeout=20)
        if res.status_code == 200:
            print(">>> 推送成功！已应用全加粗广告语。")
        else:
            print(f">>> 推送失败: {res.text}")
    except Exception as e:
        print(f">>> 请求异常: {e}")

if __name__ == "__main__":
    print("--- 启动 hao999.py 任务 ---")
    data = get_apple_ids()
    if data:
        send_to_telegram(data)
    print("--- 任务结束 ---")
