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
    """获取并解析 Apple ID"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    try:
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        driver.get("https://idfree.top/") # 目标网站
        wait = WebDriverWait(driver, 30)
        
        # 1. 点击确认按钮解除限制
        try:
            confirm_btn = wait.until(EC.element_to_be_clickable((By.ID, "confirmProceed")))
            driver.execute_script("arguments[0].click();", confirm_btn)
        except Exception as e:
            print(f"确认按钮不存在或不可点击: {e}")

        # 2. 等待 JS 渲染
        time.sleep(8) 
        
        # 3. 解析账号
        accounts = driver.find_elements(By.CSS_SELECTOR, "#accountList > div")
        account_data = []
        
        for acc in accounts:
            try:
                inputs = acc.find_elements(By.TAG_NAME, "input")
                if len(inputs) >= 2:
                    username = inputs[0].get_attribute("value")
                    password = inputs[1].get_attribute("value")
                    
                    if username and password:
                        # 格式化账号信息，使用反引号支持点击复制
                        res = (f"📍 地区：{escape_markdown('共享账号')}\n"
                               f"👤 账号：`{escape_markdown(username)}`\n"
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
    """通过发送媒体组强制图片置顶并加粗特定文本"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    
    if not content_list:
        print("未获取到有效数据，停止推送")
        return

    # 1. 顶部图片
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    # 2. 构建加粗标题和主体
    # 使用 ** 包裹 escape 后的文字
    header = f"**{escape_markdown('🚀 最新 Apple ID 共享更新')}**"
    body = "\n\n──────────────\n\n".join(content_list)
    
    # 3. 北京时间
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    # 4. 加粗警告部分
    warning_text = escape_markdown("⚠️ 警告：严禁在设置/iCloud中登录！")
    warning_section = (
        f"\n\n🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"**{warning_text}**"
    )
    
    # 5. 加粗公告内容与客服信息
    notice_val = "共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待两个小时更新，请谅解"
    announcement = (
        f"\n\n**{escape_markdown(notice_val)}**\n\n"
        f"**{escape_markdown('❤️ 欢迎关注我们频道：')}@{escape_markdown('yinlianID')}**\n"
        f"            **{escape_markdown('客    服：')}@{escape_markdown('zzyyy')}**"
    )
    
    # 组合说明文字 (Caption)
    caption = f"{header}\n\n{body}{warning_section}{announcement}"
    
    if len(caption) > 1024:
        print("警告: 消息超长，可能被截断。")

    # 6. 使用 sendMediaGroup 发送
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
        print("推送成功！文本已按要求加粗。")
    else:
        print(f"推送失败，错误详情: {res.text}")
        # 如果 Markdown 报错，尝试去掉格式化发送纯文本
        if "Bad Request: can't parse entities" in res.text:
            print("解析失败，尝试回退到纯文本模式...")
            media_group[0]['parse_mode'] = ''
            media_group[0]['caption'] = caption.replace("**", "").replace("`", "")
            payload['media'] = json.dumps(media_group)
            requests.post(url, data=payload)

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram_fixed(data)
