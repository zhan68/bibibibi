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

def send_error_to_tg(msg, photo_path=None):
    """抓取失败时，发送网页截图到频道排查原因"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not photo_path: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={'chat_id': chat_id, 'caption': f"❌ 抓取失败报告\n{msg}"}, files={'photo': photo})
    except: pass

def get_apple_ids():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        driver.get(target_url)
        
        # 使用隐式智能等待，直到页面上渲染出带有 "border-success" 的正常账号绿色卡片
        print("等待动态 Vue/React 组件解密渲染绿色正常卡片...")
        wait = WebDriverWait(driver, 20)
        
        # 核心策略：直接定位正常卡片（绿框 border-success）
        # 这样就自动过滤掉了红框（border-danger 状态异常）的卡片！
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".card.border-success")))
        
        # 提取所有状态为“正常”的绿色卡片
        success_cards = driver.find_elements(By.CSS_SELECTOR, ".card.border-success")
        print(f"分析完毕：成功锁定 {len(success_cards)} 个状态正常的绿色账号卡片")
        
        account_data = []
        
        for card in success_cards:
            try:
                # 1. 提取账号：直接在卡片顶部的 h5 标签中抓取明文
                h5_element = card.find_element(By.TAG_NAME, "h5")
                username = h5_element.text.strip()
                
                # 清洗账号，防止里面残留图标或空格
                username = re.sub(r'^[^\w]+', '', username) 
                
                # 2. 精准寻找卡片内部的按钮
                # 有些老毛面板的复制账号和复制密码按钮带有单独的 class 区分，这里直接捞取所有的 button
                buttons = card.find_elements(By.TAG_NAME, "button")
                if not buttons:
                    # 兼容类似 a 标签或者带 .btn 类名的伪按钮
                    buttons = card.find_elements(By.CSS_SELECTOR, "a, .btn, [class*='copy']")
                
                password = ""
                # 3. 从这块正常卡片内部所有的按钮中，提取藏在属性里的密码
                for btn in buttons:
                    clip_text = btn.get_attribute("data-clipboard-text") or btn.get_attribute("data-text")
                    if clip_text:
                        clip_text = clip_text.strip()
                        # 密码特征：不包含账号，不是邮箱，长度在 5 位以上
                        if clip_text != username and "@" not in clip_text and len(clip_text) >= 5:
                            password = clip_text
                            break
                
                # 如果没在属性里抓到密码，尝试第二种老毛面板特征：第二个按钮通常是密码按钮，点击它或拿它的文本
                if not password and len(buttons) >= 2:
                    password = buttons[1].get_attribute("data-clipboard-text") or buttons[1].text.strip()

                if username and password and "@" in username:
                    res = (f"👤 账号：`{escape_markdown(username)}`\n"
                           f"🔑 密码：`{escape_markdown(password)}`")
                    
                    if res not in account_data:
                        account_data.append(res)
                        print(f"🎉【抓取成功】状态正常 -> 账号: {username} | 密码: {password}")
            except Exception as inner_e:
                continue
                
        driver.quit()
        return account_data
        
    except Exception as e:
        scr_path = "error_moe.png"
        try:
            driver.save_screenshot(scr_path)
            send_error_to_tg(f"抓取发生崩溃，已发送截图: {str(e)[:100]}", scr_path)
        except: pass
        driver.quit()
        return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not content_list: 
        print("没有读取到任何[状态正常]的有效账号，取消推送。")
        return

    body = "\n\n──────────────\n\n".join(content_list)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    notice = (
        f"🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"⚠️ *警告：严禁在设置/iCloud中登录！*\n\n"
        f"*共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待15分钟更新，请谅解*\n\n"
        f"❤️ *欢迎关注我们频道：*@{escape_markdown('yinlianID')}\n"
        f"            *客    服：*@{escape_markdown('zzyyy')}"
    )
    
    header = "🚀 *最新 Apple ID 共享更新【5】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    data = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    
    if len(full_caption) > 1020:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    res = requests.post(url, json=data)
    print(f"TG 发送完成，状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
