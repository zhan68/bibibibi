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
            requests.post(url, data={'chat_id': chat_id, 'caption': f"❌ 源3抓取失败报告\n{msg}"}, files={'photo': photo})
    except: pass

def get_apple_ids():
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    # 模拟标准桌面浏览器，确保防爬虫策略不会隐藏隐藏属性
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        driver.get(target_url)
        
        # 针对此类面板，给足 8 秒确保后台状态接口加载并刷新完毕
        print("等待网页卡片和状态渲染 (8秒)...")
        time.sleep(8)
        
        # 定位页面上所有的独立账号卡片模块（通常每个账号密码都在单独的块或行中）
        # 这里使用多重容器定位，确保把每一个红框/绿框卡片都捕获到
        cards = driver.find_elements(By.XPATH, "//div[contains(@class, 'panel') or contains(@class, 'card') or contains(@style, 'border')]")
        
        # 兜底：如果上面的多选择器没抓到，就直接抓取所有的复制账号按钮，然后反向找它们各自的包裹外壳
        if not cards:
            user_btns_fallback = driver.find_elements(By.XPATH, "//*[contains(text(), '复制账号')]")
            cards = [btn.find_element(By.XPATH, "./ancestor::div[position()<=4]") for btn in user_btns_fallback]
            
        print(f"分析完毕：共定位到 {len(cards)} 个账号数据卡片")
        
        account_data = []
        
        for index, card in enumerate(cards):
            card_text = card.text
            if not card_text:
                continue
            
            # 核心过滤：只有当这个卡片明确包含“状态正常”或者“正常”时才进入
            if "状态正常" in card_text or "正常" in card_text:
                if "状态异常" in card_text or "异常" in card_text:
                    continue # 排除可能包含异常的干扰卡片
                
                try:
                    # 在当前正常卡片的内部，精准寻找对应的复制账号和复制密码按钮
                    user_btn = card.find_element(By.XPATH, ".//*[contains(text(), '账号') or contains(@class, 'user') or contains(@class, 'copy')]")
                    pass_btn = card.find_element(By.XPATH, ".//*[contains(text(), '密码') or contains(@class, 'pass')]")
                    
                    # 关键破局点：优先提取老毛面板中隐藏在属性里的真实账号密码明文
                    username = user_btn.get_attribute("data-clipboard-text") or user_btn.get_attribute("data-text")
                    password = pass_btn.get_attribute("data-clipboard-text") or pass_btn.get_attribute("data-text")
                    
                    # 兜底清洗：如果属性里没藏，说明可能用正则能从卡片内部标签洗出来
                    if not username:
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', card_text)
                        if email_match:
                            username = email_match.group(0)
                    
                    # 如果拿到了数据，过滤掉非法项后加入队列
                    if username and password and "@" in username:
                        res = (f"👤 账号：`{escape_markdown(username.strip())}`\n"
                               f"🔑 密码：`{escape_markdown(password.strip())}`")
                        
                        if res not in account_data:
                            account_data.append(res)
                            print(f"🎉【抓取成功】发现正常账号并成功提取明文: {username.strip()}")
                except Exception as inner_e:
                    # 单个卡片提取失败，跳过，不影响整体循环
                    continue
                    
        driver.quit()
        return account_data
        
    except Exception as e:
        scr_path = "error_moe.png"
        try:
            driver.save_screenshot(scr_path)
            send_error_to_tg(f"源3抓取异常: {str(e)[:100]}", scr_path)
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
    
    header = "🚀 *最新 Apple ID 共享更新【3】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    # 强制图片置顶逻辑
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
