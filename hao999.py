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

def get_apple_ids():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # 目标网址
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        driver.get(target_url)
        wait = WebDriverWait(driver, 30)
        
        # 等待文档内容加载完成（这里根据该文档系统的通用表格特征等待 tr 或 td 渲染）
        print("等待文档数据加载...")
        wait.until(EC.presence_of_element_located((By.TAG_NAME, "table")))
        time.sleep(5)  # 稍微延迟，确保数据完全从后端加载并渲染出来
        
        account_data = []
        
        # 抓取表格中所有的行 (Row)
        rows = driver.find_elements(By.TAG_NAME, "tr")
        print(f"共检测到 {len(rows)} 行数据，开始解析...")

        for row in rows:
            # 获取当前行里的所有单元格 (Cell)
            cells = row.find_elements(By.TAG_NAME, "td")
            
            # 如果单元格数量太少，说明不是有效的数据行（通常账号表格至少有 3 列以上：账号、密码、状态、地区等）
            if len(cells) < 3:
                continue
                
            # 将整行中每个格子的文本提取出来
            row_text = [cell.text.strip() for cell in cells]
            
            # 将整行文本合并成一个字符串，用来查找关键字
            combined_text = "".join(row_text)
            
            # 核心过滤：只有当这一行包含 "状态正常" 或 "正常" 时才进行解析
            if "状态正常" in combined_text or "正常" in combined_text:
                username = ""
                password = ""
                region = "源2-共享" # 默认地区
                
                # 正则匹配查找账号（通常是邮箱格式）
                for text in row_text:
                    if "@" in text and "." in text and not username:
                        username = text
                        continue
                    # 匹配可能是密码的列（排除常见的中文状态和邮箱，剩下长得像密码的）
                    if text and not any(x in text for x in ["正常", "锁定", "更新", "检测", "@", "http"]):
                        # 简单过滤掉太短或含有大段中文的干扰项
                        if len(text) >= 4 and not re.search(r'[\u4e00-\u9fa5]', text):
                            password = text

                # 如果成功提取到了账号和密码，则组装数据
                if username and password:
                    res = (f"📍 地区：{escape_markdown(region)}\n"
                           f"👤 账号：`{escape_markdown(username)}`\n"
                           f"🔑 密码：`{escape_markdown(password)}`")
                    account_data.append(res)
                    print(f"成功锁定正常账号: {username}")

        driver.quit()
        return account_data

    except Exception as e:
        print(f"抓取过程崩溃: {e}")
        screenshot_path = "error_debug.png"
        try:
            driver.save_screenshot(screenshot_path)
            send_error_to_tg(f"抓取崩溃日志: {e}", screenshot_path)
        except:
            pass
        driver.quit()
        return None

def send_error_to_tg(msg, photo_path=None):
    """当抓取失败时，发送截图到 Telegram 方便排查"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={'chat_id': chat_id, 'caption': f"❌ 脚本运行失败报告\n{msg}"}, files={'photo': photo})
    except Exception as e:
        print(f"发送错误日志失败: {e}")

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not content_list: 
        print("没有获取到有效账号，取消发送。")
        return

    # 1. 组装消息
    body = "\n\n──────────────\n\n".join(content_list)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    notice = (
        f"🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"⚠️ *警告：严禁在设置/iCloud中登录！*\n\n"
        f"*共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待两个小时更新，请谅解*\n\n"
        f"❤️ *欢迎关注我们频道：*@{escape_markdown('yinlianID')}\n"
        f"          *客    服：*@{escape_markdown('zzyyy')}"
    )
    
    header = "🍎 *最新 Apple ID 共享更新【5】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    # 2. 发送逻辑：优先图片模式，超长则切换文字模式
    if len(full_caption) < 1020:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    res = requests.post(url, json=payload)
    print(f"TG 发送状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
