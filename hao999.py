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
    
    # 调整窗口分辨率，彻底模拟一台标准的桌面电脑，强制网页加载完整 DOM 树
    chrome_options.add_argument('--window-size=1920,1080')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        driver.get(target_url)
        
        # 针对该面板，给予 10 秒时间确保所有卡片文本解密完毕
        print("等待网页卡片和状态渲染 (10秒)...")
        time.sleep(10)
        
        account_data = []

        # 【核心黑科技】：彻底抛弃 class 类名依赖，直接抓取页面上所有写着 "复制账号" 的元素
        user_buttons = driver.find_elements(By.XPATH, "//*[contains(text(), '复制账号')]")
        print(f"分析完毕：共定位到 {len(user_buttons)} 组潜在账号按钮")
        
        for btn in user_buttons:
            try:
                # 寻找这个按钮往上走能包裹住“当前整个红框/绿框”的最近一层外壳父节点
                # 我们通过 ancestor::div[position()<=5] 向上连追 5 层，直接把父壳提取出来
                parent_card = btn.find_element(By.XPATH, "./ancestor::div[contains(@class, 'panel') or contains(@class, 'card') or contains(@class, 'item') or position()<=3]")
                card_text = parent_card.text
                
                # 只要发现这块数据里写着“正常”或“状态正常”，且没有被锁定的标志
                if "正常" in card_text:
                    if "异常" in card_text or "锁定" in card_text:
                        continue # 被拦截：属于异常或锁定状态，跳过
                    
                    # 在这一个卡片的范围内，去抠“复制账号”和“复制密码”两个按钮
                    acc_btn = parent_card.find_element(By.XPATH, "//*[contains(text(), '复制账号')]")
                    pwd_btn = parent_card.find_element(By.XPATH, "//*[contains(text(), '复制密码')]")
                    
                    # 抓取绑定的隐藏真实明文属性
                    username = acc_btn.get_attribute("data-clipboard-text") or acc_btn.get_attribute("data-text")
                    password = pwd_btn.get_attribute("data-clipboard-text") or pwd_btn.get_attribute("data-text")
                    
                    # 如果隐藏属性由于无头浏览器被隐藏，通过备用方案：直接用正则从父壳子文本里把可能出现的邮箱榨取出来
                    if not username or "@" not in str(username):
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', card_text)
                        if email_match:
                            username = email_match.group(0)
                    
                    if username and password:
                        res = (f"👤 账号：`{escape_markdown(username.strip())}`\n"
                               f"🔑 密码：`{escape_markdown(password.strip())}`")
                        
                        if res not in account_data:
                            account_data.append(res)
                            print(f"🎉【抓取成功】状态正常 -> 成功抓取账号: {username.strip()}")
            except Exception as inner_e:
                # 如果单个卡片解析出错，不破坏大循环，继续往下找
                continue

        # 【终极兜底策略】：如果上述逻辑依然因为 DOM 隔离被返回 0，使用不依赖任何层级的“元素全排列洗数据法”
        if not account_data:
            print("⚠️ 层级卡片查找失败，触发系统终极文本流平铺提取法...")
            all_elements = driver.find_elements(By.XPATH, "//*[contains(@data-clipboard-text, '@')]")
            for el in all_elements:
                u = el.get_attribute("data-clipboard-text")
                if u and "@" in u:
                    print(f"🔍 兜底检测到属性中藏匿有账号: {u}")
                    # 寻找紧邻它的下一个元素作为密码
                    try:
                        p_el = el.find_element(By.XPATH, "./following-sibling::*[1]")
                        p = p_el.get_attribute("data-clipboard-text") or p_el.text
                        if p and len(p) >= 5:
                            res = (f"👤 账号：`{escape_markdown(u.strip())}`\n"
                                   f"🔑 密码：`{escape_markdown(p.strip())}`")
                            account_data.append(res)
                    except: pass
                    
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
