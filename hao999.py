import os
import requests
import time
import re
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
    # 模拟常见浏览器，防止被拦截
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        driver.get(target_url)
        
        # 强制等待 8 秒，给网页的 JavaScript 和网络请求充足的时间来渲染出文字内容
        print("等待网页异步数据加载中 (8秒)...")
        time.sleep(8)
        
        # 直接抓取整个页面的所有可见文本
        page_text = driver.find_element(By.TAG_NAME, "body").text
        print("网页文本获取成功，开始分析数据...")
        
        account_data = []
        
        # 核心逻辑：按行切分网页文本进行检查
        lines = page_text.split('\n')
        print(f"当前页面共解析出 {len(lines)} 行文本")
        
        for index, line in enumerate(lines):
            # 只有当前行或者紧接着的下一行包含“正常”或“状态正常”时，才视为有效账号段落
            if "状态正常" in line or "正常" in line:
                # 寻找上下 3 行范围内的邮箱（账号）和密码
                search_range = lines[max(0, index-2):min(len(lines), index+3)]
                combined_context = " ".join(search_range)
                
                # 正则表达式匹配邮箱账号
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', combined_context)
                
                if email_match:
                    username = email_match.group(0)
                    password = ""
                    
                    # 在这几行里寻找密码
                    # 密码的特征：通常不含@、不含中文、不含网址、长度在5-25位之间
                    words = combined_context.split()
                    for word in words:
                        word = word.strip()
                        if word == username:
                            continue
                        if "@" not in word and "http" not in word and not re.search(r'[\u4e00-\u9fa5]', word):
                            # 过滤掉一些状态词和多余的特殊符号
                            if len(word) >= 5 and word not in ["状态正常", "正常", "密码：", "账号：", "状态："]:
                                # 进一步清洗可能残留在密码前后的中文冒号等
                                clean_word = re.sub(r'^[账号密码状态\s：:]+', '', word)
                                if len(clean_word) >= 5:
                                    password = clean_word
                                    break
                    
                    if username and password:
                        res = (f"📍 地区：{escape_markdown('源2-共享')}\n"
                               f"👤 账号：`{escape_markdown(username)}`\n"
                               f"🔑 密码：`{escape_markdown(password)}`")
                        
                        # 防止重复添加同一个账号
                        if res not in account_data:
                            account_data.append(res)
                            print(f"✅ 成功提取到状态正常的账号: {username}")

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
    
    header = "🍎 *最新 Apple ID 共享更新（备用源）*"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    full_caption = f"{header}\n\n{body}\n\n{notice}"

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
