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
    """专门为 Render Docker 环境配置的浏览器启动器"""
    chrome_options = Options()
    # --- 核心云端运行参数 ---
    [span_0](start_span)chrome_options.add_argument('--headless')           # 无界面模式[span_0](end_span)
    [span_1](start_span)chrome_options.add_argument('--no-sandbox')         # 必须：解决权限问题[span_1](end_span)
    [span_2](start_span)chrome_options.add_argument('--disable-dev-shm-usage') # 必须：防止内存溢出[span_2](end_span)
    chrome_options.add_argument('--disable-gpu')        # 禁用GPU节省资源
    
    # 指定 Chrome 二进制文件路径 (Render 镜像默认路径)
    [span_3](start_span)chrome_options.binary_location = "/usr/bin/google-chrome"[span_3](end_span)
    
    # 禁止加载图片，大幅减少内存占用 (Render 只有 512MB)
    chrome_options.add_experimental_option("prefs", {"profile.managed_default_content_settings.images": 2})
    
    # 模拟真实设备 UA
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    return driver

def get_apple_ids():
    driver = None
    try:
        driver = start_browser()
        print(">>> [hao456] 正在访问数据源...")
        driver.get("https://xdd.net.tr/share/wRjpcyhumY") 
        wait = WebDriverWait(driver, 30) # 延长等待时间
        
        # 1. 密码解锁逻辑
        print(">>> [hao456] 正在输入解锁密码...")
        pwd_input = wait.until(EC.presence_of_element_located((By.TAG_NAME, "input")))
        pwd_input.clear()
        pwd_input.send_keys("7778")
        
        submit_btn = driver.find_element(By.CSS_SELECTOR, "button, .btn-primary")
        driver.execute_script("arguments[0].click();", submit_btn)
        
        # 增加等待跳转和加载的时间
        time.sleep(12) 
        
        # 2. 解析账号数据
        print(">>> [hao456] 正在提取页面数据...")
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "copy-btn")))
        
        user_btns = driver.find_elements(By.CLASS_NAME, "copy-btn")
        pass_btns = driver.find_elements(By.CLASS_NAME, "copy-pass-btn")
        
        account_data = []
        for i in range(min(len(user_btns), len(pass_btns))):
            username = user_btns[i].get_attribute("data-clipboard-text") or user_btns[i].text.strip()
            password = pass_btns[i].get_attribute("data-clipboard-text") or pass_btns[i].text.strip()
            
            # 过滤无效信息
            if username and password and "@" in username and "http" not in username.lower():
                res = (f"👤 账号：`{escape_markdown(username)}`\n"
                       f"🔑 密码：`{escape_markdown(password)}`")
                account_data.append(res)
        
        print(f">>> [hao456] 成功抓取到 {len(account_data)} 个账号")
        return account_data

    except Exception as e:
        print(f"❌ [hao456] 抓取失败: {e}")
        return None
    finally:
        if driver:
            print(">>> [hao456] 正在关闭浏览器释放内存...")
            [span_4](start_span)driver.quit() # 必须执行，否则会阻塞下一个脚本运行[span_4](end_span)

def send_to_telegram(content_list):
    [span_5](start_span)token = os.environ.get('BOT_TOKEN') # 从 Render 环境获取[span_5](end_span)
    chat_id = "@yinlianID"
    if not content_list: return

    body = "\n\n──────────────\n\n".join(content_list)
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    
    header = "🚀 *最新 Apple ID 共享更新【2】*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n🕒 更新时间：{escape_markdown(bj_time)}\n❤️ 关注频道：@yinlianID"

    # 发送逻辑
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    data = {"chat_id": chat_id, "photo": img_url, "caption": full_caption, "parse_mode": "MarkdownV2"}
    
    # 处理字数超限
    if len(full_caption) > 1024:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": f"[​]({img_url}){full_caption}", "parse_mode": "MarkdownV2"}
    
    res = requests.post(url, json=data)
    print(f">>> [hao456] 推送结果: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    if data:
        send_to_telegram(data)
    else:
        print(">>> [hao456] 抓取结果为空，任务结束。")
