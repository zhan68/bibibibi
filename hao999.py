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
    # 模拟真实的高版本浏览器，防止文档系统识别为爬虫而锁死数据
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        driver.get(target_url)
        
        # [span_1](start_span)针对加密型文档，给足 10 秒时间等待内部的解密 JS 执行完毕[span_1](end_span)
        print("等待网页异步解密数据中 (10秒)...")
        time.sleep(10)
        
        account_data = []

        # 【核心黑科技】：利用 JS 注入，直接绕过 DOM 框架限制，把整个页面能看见的所有元素文本全部捞出来
        # 并且强制每一行的单元格之间用 " | " 分隔，换行用 "\n" 分隔。这可以物理碾压任何文档结构！
        js_extractor = """
        let results = [];
        let rows = document.querySelectorAll('tr, .row, .grid-row, div[role="row"]');
        if (rows.length > 0) {
            rows.forEach(r => {
                let cells = r.querySelectorAll('td, .cell, .grid-cell, div[role="gridcell"]');
                if (cells.length > 0) {
                    let cellTexts = Array.from(cells).map(c => c.innerText.strip || c.innerText).filter(t => t);
                    if (cellTexts.length > 0) results.push(cellTexts.join(' | '));
                }
            });
        }
        if (results.length === 0) {
            // 如果没抓到标准行，直接退回到抓取所有 DIV/SPAN
            return document.body.innerText;
        }
        return results.join('\\n');
        """
        
        page_raw_text = driver.execute_script(js_extractor)
        driver.quit()
        
        print("--- 抓取到的底层数据快照 ---")
        lines = [l.strip() for l in page_raw_text.split('\n') if l.strip()]
        print(f"成功将页面打散为 {len(lines)} 条独立数据链")
        
        for line in lines:
            # [span_2](start_span)调试打印，方便你在 GitHub Actions 中一眼看出它抓到了什么[span_2](end_span)
            print(f"正在分析链条: {line}")
            
            # 条件一：只要这行数据里包含了 “正常” 或者 “状态正常”
            if "正常" in line:
                # 使用灵活的正则把邮箱（账号）给提取出来
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', line)
                
                if email_match:
                    username = email_match.group(0)
                    password = ""
                    
                    # 将这行用分隔符拆开，寻找符合密码特征的那个字段
                    parts = [p.strip() for p in re.split(r'[\s|｜,，;；\t]+', line)]
                    for part in parts:
                        if part == username:
                            continue
                        # 密码通常不能含有中文、不能含@、不能含网址，且长度要在 5 到 20 位之间
                        if not re.search(r'[\u4e00-\u9fa5]', part) and "@" not in part and "http" not in part:
                            if 5 <= len(part) <= 20:
                                password = part
                                break
                    
                    # 只有账号密码同时齐活了才算成功
                    if username and password:
                        res = (f"📍 地区：{escape_markdown('源2-共享')}\n"
                               f"👤 账号：`{escape_markdown(username)}`\n"
                               f"🔑 密码：`{escape_markdown(password)}`")
                        
                        if res not in account_data:
                            account_data.append(res)
                            print(f"🎉【抓取成功】状态正常 -> 账号: {username} | 密码: {password}")
                            
        return account_data

    except Exception as e:
        print(f"抓取过程崩溃: {e}")
        try: driver.quit() 
        except: pass
        return None

def send_to_telegram(content_list):
    [span_3](start_span)token = os.environ.get('BOT_TOKEN')[span_3](end_span)
    chat_id = "@yinlianID"
    if not content_list: 
        [span_4](start_span)print("没有获取到有效账号，取消发送。")[span_4](end_span)
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
    print(f"TG 发送状态: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
