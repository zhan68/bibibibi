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

def start_browser():
    """统一配置浏览器，适配 Render Docker 环境"""
    chrome_options = Options()
    # --- Render 生产环境必须参数 ---
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')
    # 显式指定 Chrome 路径
    chrome_options.binary_location = "/usr/bin/google-chrome" 
    # 内存优化：禁止加载图片
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def send_error_to_tg(msg, photo_path=None):
    """抓取失败时发送报告"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not photo_path: return
    
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        with open(photo_path, 'rb') as photo:
            requests.post(url, data={'chat_id': chat_id, 'caption': f"❌ 源3抓取失败报告\n{msg}"}, files={'photo': photo})
    except Exception as e:
        print(f"发送报错通知失败: {e}")

def get_apple_ids():
    driver = None
    try:
        driver = start_browser()
        print(">>> 正在访问源3(Moe)页面...")
        driver.get("https://appleid.moe233.app/share/GURdOstilD")
        wait = WebDriverWait(driver, 30)
        
        # 等待关键按钮加载
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "copy-btn")))
        
        user_btns = driver.find_elements(By.CSS_SELECTOR, ".copy-btn")
        pass_btns = driver.find_elements(By.CSS_SELECTOR, ".copy-pass-btn")
        
        account_data = []
        for i in range(min(len(user_btns), len(pass_btns))):
            username = user_btns[i].get_attribute("data-clipboard-text") or user_btns[i].text.strip()
            password = pass_btns[i].get_attribute("data-clipboard-text") or pass_btns[i].text.strip()
            
            # 过滤无效项
            if not username or "@" not in username or "http" in username.lower():
                continue
                
            res = (f"👤 账号：`{escape_markdown(username)}`\n"
                   f"🔑 密码：`{escape_markdown(password)}`")
            account_data.append(res)
        
        print(f"成功抓取到 {len(account_data)} 个账号。")
        return account_data

    except Exception as e:
        print(f"❌ hao789 运行异常: {e}")
        if driver:
            try:
                scr_path = "error_hao789.png"
                driver.save_screenshot(scr_path)
                send_error_to_tg(f"hao789 抓取异常: {str(e)[:100]}", scr_path)
            except: pass
        return None
    finally:
        if driver:
            print("正在关闭浏览器并释放资源...")
            driver.quit()

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not token or not content_list: return

    body = "\n\n──────────────\n\n".join(content_list)
    # 北京时间计算
    bj_time = (datetime.now(timezone.utc) + timedelta(hours=8)).strftime('%Y-%m-%d %H:%M:%S')
    
    header = "🚀 *最新 Apple ID 共享更新【3】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    # 广告内容
    ad_text = (
        "共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，"
        "请持续关注频道等待两个小时更新，请谅解\n\n"
        "❤️ 欢迎关注我们频道：@yinlianID\n"
        "            客    服：@zzyyy"
    )

    # 组合成完整的 caption
    full_caption = (
        f"{header}\n\n{body}\n\n"
        f"🕒 更新时间：{escape_markdown(bj_time)}\n"
        f"⚠️ *严禁在设置/iCloud中登录！*\n\n"
        f"──────────────\n\n"
        f"{escape_markdown(ad_text)}"
    )

    # Telegram 发送逻辑
    if len(full_caption) <= 1024:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        data = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    else:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    requests.post(url, json=data)

if __name__ == "__main__":
    print("--- 启动 hao789.py 任务 ---")
    data = get_apple_ids()
    if data:
        send_to_telegram(data)
    print("--- hao789.py 任务执行结束 ---")
