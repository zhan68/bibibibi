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
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_apple_ids():
    chrome_options = Options()
    
    # 💡 核心自愈补丁：直接锁定系统原生 Chrome 路径，彻底抛弃饱含 Bug 的 DriverManager
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument('--headless=new')             # 使用推荐的全新无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')               # 禁用 GPU 防止 Linux 容器内卡死
    
    # 💡 反爬虫高级伪装参数：彻底抹除自动化痕迹，防止被 CF 盾拦截
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--lang=zh-CN,zh;q=0.9')
    
    # 模拟真实移动端 User-Agent，降低被封概率
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

    try:
        print("🚀 [通道 2] 正在直接调动系统原生 Chrome 驱动开跑...")
        driver = webdriver.Chrome(options=chrome_options)
        
        print("[通道 2] 开始访问页面...")
        driver.get("https://xdd.net.tr/share/wRjpcyhumY")
        wait = WebDriverWait(driver, 30)
        
        # --- 1. 强力密码解锁逻辑 ---
        try:
            print("[通道 2] 正在寻找密码输入框...")
            pwd_input = wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
            pwd_input.clear()
            pwd_input.send_keys("7778")
            
            submit_btn = driver.find_element(By.CSS_SELECTOR, "button, .btn-primary, input[type='submit']")
            driver.execute_script("arguments[0].click();", submit_btn)
            print("[通道 2] 密码已提交，启动多卡片数量动态嗅探...")
            
            # 💡 核心改良：放弃盲目死等 12 秒，在 15 秒内高频检测，直到卡片数量 >= 2 判定全量渲染齐全
            for check_loop in range(15):
                user_btns = driver.find_elements(By.CLASS_NAME, "copy-btn")
                if len(user_btns) >= 2:
                    print(f"🎉 [通道 2] 动态监测成功！检测到全量 {len(user_btns)} 组卡片已加载就位，提前唤醒抓取！")
                    break
                time.sleep(1)
                
            time.sleep(2) # 额外多留 2 秒作为平稳缓冲，确保对应的密码按钮渲染完毕
        except Exception as e:
            print(f"[通道 2] 密码环节或数量监测处理异常: {e}")

        # --- 2. 账号解析与过滤逻辑 ---
        print("[通道 2] 正在解析全量账号数据...")
        user_btns = driver.find_elements(By.CLASS_NAME, "copy-btn")
        pass_btns = driver.find_elements(By.CLASS_NAME, "copy-pass-btn")
        
        account_data = []
        for i in range(min(len(user_btns), len(pass_btns))):
            username = user_btns[i].get_attribute("data-clipboard-text") or user_btns[i].text.strip()
            password = pass_btns[i].get_attribute("data-clipboard-text") or pass_btns[i].text.strip()
            
            if "http" in username.lower() or "/" in username:
                continue
                
            if username and password:
                res = (f"👤 账号：`{escape_markdown(username)}`\n"
                       f"🔑 密码：`{escape_markdown(password)}`")
                if res not in account_data:
                    account_data.append(res)
        
        driver.quit()
        return account_data

    except Exception as e:
        print(f"❌ [通道 2] 抓取过程崩溃: {e}")
        screenshot_path = "error_debug.png"
        try:
            driver.save_screenshot(screenshot_path)
            send_error_to_tg(f"通道 2 抓取崩溃日志: {e}", screenshot_path)
        except:
            pass
        try:
            driver.quit()
        except:
            pass
        return None

def send_error_to_tg(msg, photo_path=None):
    """当抓取失败时，发送截图到 Telegram 方便排查"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not token or not photo_path: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={'chat_id': chat_id, 'caption': f"❌ 脚本运行失败报告\n{msg}"}, files={'photo': photo})
    except:
        pass

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not content_list: 
        print("⚠️ [通道 2] 未获取到有效数据，或当前网站无更新，取消本次 TG 推送。")
        return

    print(f"🎉 [通道 2] 成功抓取到 {len(content_list)} 组账号，正在组织排版向 TG 推送...")
    body = "\n\n──────────────\n\n".join(content_list)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    notice = (
        f"🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"⚠️ *警告：严禁在设置/iCloud中登录！*\n\n"
        f"*共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待15分钟更新，请谅解*\n\n"
        f"❤️ *欢迎关注我们交流群：*@{escape_markdown('bh888')}\n"
        f"          *客    服：*@{escape_markdown('zzyyy')}"
    )
    
    header = "🚀 *最新 Apple ID 共享更新【2】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

    if len(full_caption) < 1020:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        payload = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    requests.post(url, json=payload)

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
