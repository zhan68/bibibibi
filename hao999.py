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
    # 使用现代桌面浏览器 User-Agent，防止在线文档对移动端进行特殊的动态样式混淆
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        driver.get(target_url)
        
        # 加大等待时间，给足在线文档解密和渲染表格的时间
        print("等待网页动态数据渲染 (10秒)...")
        time.sleep(10)
        
        account_data = []
        
        # 抓取页面中所有可能构成行、段落或单元格集合的容器节点
        # 这可以物理碾压 <tr>、类名为 row 的 div 或者是纯文本行的 p
        elements = driver.find_elements(By.CSS_SELECTOR, 'tr, .row, .grid-row, p, div[class*="line"], div[class*="row"]')
        print(f"共扫描到可能包含数据的节点: {len(elements)} 个")
        
        for element in elements:
            try:
                line_text = element.text
                if not line_text:
                    continue
                
                # 将同一行/块内的换行文本，使用 " | " 拼起来变成规整的长文本字符串
                clean_line = " | ".join([part.strip() for part in line_text.split("\n") if part.strip()])
                
                # 核心过滤判定：当前行内必须包含“状态正常”或“正常”
                if "正常" in clean_line or "状态正常" in clean_line:
                    # 排除已经锁定的干扰项
                    if "锁定" in clean_line or "异常" in clean_line:
                        continue
                        
                    # 1. 提取邮箱账号
                    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', clean_line)
                    
                    if email_match:
                        username = email_match.group(0)
                        password = ""
                        
                        # 2. 将整行切碎，寻找最像密码的独立字符串
                        parts = [p.strip() for p in re.split(r'[\s|｜,，;；\t:]+', clean_line)]
                        for part in parts:
                            if part == username or not part:
                                continue
                            
                            # 密码特征判定：不能包含中文、不含@、不含网址，长度在 5 到 22 位之间
                            if not re.search(r'[\u4e00-\u9fa5]', part) and "@" not in part and "http" not in part:
                                if 5 <= len(part) <= 22 and part not in ["正常", "状态正常"]:
                                    password = part
                                    break
                        
                        # 3. 只有账号和密码成功匹配才加入
                        if username and password:
                            res = (f"👤 账号：`{escape_markdown(username)}`\n"
                                   f"🔑 密码：`{escape_markdown(password)}`")
                            
                            if res not in account_data:
                                account_data.append(res)
                                print(f"✅ [状态正常] 成功捕获账号: {username}")
            except:
                continue # 单行节点若提取失败，跳过并继续，防止因个别节点死循环
                
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
    
    header = "🚀 *最新 Apple ID 共享更新【5】*"
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
