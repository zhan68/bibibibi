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
    # 强制注入标准桌面分辨率，防止防爬脚本判定无头
    chrome_options.add_argument('--window-size=1440,900')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # 设定全局页面加载超时和脚本执行超时为 15 秒，绝不允许在 GitHub Actions 中卡死
    driver.set_page_load_timeout(15)
    driver.set_script_timeout(15)
    
    try:
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        
        try:
            driver.get(target_url)
        except Exception as load_e:
            # 即使因为反爬请求挂起导致加载未完全完成，只要 DOM 树出来了，我们继续往下走
            print("页面加载触发超时保护或未完全载入，开始尝试强制提取已渲染数据...")
            
        # 强制静默睡眠 6 秒，给解密 JS 脚本留出充裕的执行时间
        time.sleep(6)
        
        account_data = []
        
        # 终极定位：抓取带有邮箱的所有文本块，或者带有 card/panel 类名的卡片容器
        cards = driver.find_elements(By.CSS_SELECTOR, ".card, .panel, div[class*='card'], div[style*='border']")
        
        # 兜底：如果被混淆了类名，直接抓取包含“复制”字样的容器
        if not cards:
            fallback_elements = driver.find_elements(By.XPATH, "//*[contains(text(), '复制')]/..")
            cards = fallback_elements

        print(f"嗅探分析完毕：在当前 DOM 环境下共捕捉到 {len(cards)} 个潜在数据链块")
        
        for card in cards:
            try:
                card_text = card.text
                if not card_text:
                    continue
                
                # 核心过滤：只有状态包含“正常”，且排除“异常”和“锁定”
                if "正常" in card_text:
                    if "异常" in card_text or "锁定" in card_text:
                        continue
                    
                    # 1. 提取账号：直接用正则匹配卡片块内的邮箱
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', card_text)
                    if not email_match:
                        continue
                    username = email_match.group(0).strip()
                    
                    # 2. 精准捞取当前区块内的按钮，从中提取隐藏的密码
                    password = ""
                    buttons = card.find_elements(By.CSS_SELECTOR, "button, .btn, a, [data-clipboard-text]")
                    
                    for btn in buttons:
                        val = btn.get_attribute("data-clipboard-text") or btn.get_attribute("data-text")
                        if val:
                            val = val.strip()
                            # 过滤掉和账号相同的属性，剩下的就是密码
                            if val != username and "@" not in val and len(val) >= 4:
                                password = val
                                break
                    
                    # 3. 如果隐藏属性里什么都没装，使用兜底机制：把整行切碎，找出不含中文和特殊符号、长度大于 5 的字符串作为密码
                    if not password:
                        parts = [p.strip() for p in re.split(r'[\s|｜,，;；\t:]+', card_text)]
                        for part in parts:
                            if part != username and len(part) >= 5:
                                if not re.search(r'[\u4e00-\u9fa5]', part) and "@" not in part and "2026-" not in part:
                                    password = part
                                    break
                    
                    if username and password:
                        res = (f"👤 账号：`{escape_markdown(username)}`\n"
                               f"🔑 密码：`{escape_markdown(password)}`")
                        
                        if res not in account_data:
                            account_data.append(res)
                            print(f"🎉【过滤通过】账号: {username} | 密码: {password}")
            except:
                continue
                
        driver.quit()
        return account_data

    except Exception as e:
        print(f"❌ 混合收割链条运行崩溃: {e}")
        try: driver.quit()
        except: pass
        return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not content_list: 
        print("没有读取到任何[状态正常]的有效账号，取消本次 TG 推送。")
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
    
    header = "🚀 *最新 Apple ID 共享更新【3】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    data = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    
    if len(full_caption) > 1020:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    res = requests.post(url, json=data)
    print(f"TG 推送完成，状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
