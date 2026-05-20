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
    chrome_options.add_argument('--window-size=1440,900')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    
    # 💡 核心补丁：强行给 headless 浏览器注入字体，防止乱码导致 JS 解密挂起
    chrome_options.add_argument('--lang=zh-CN')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false') # 禁用图片，极大加快加载速度

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    # 设置 25 秒强制超时，绝不在 Actions 中死锁
    driver.set_page_load_timeout(25)
    driver.set_script_timeout(25)
    
    try:
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"开始访问页面: {target_url}")
        
        try:
            driver.get(target_url)
        except Exception as load_e:
            print("页面到达硬性载入边界，开始强制提取当前 DOM 缓存数据...")
            
        # 静默等待 8 秒，给动态框架充足的渲染时间
        time.sleep(8)
        
        account_data = []
        
        # 探测全页面所有的框架上下文（穿透内置 iframe 容器）
        all_frames = ["main_page"]
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for idx, frame in enumerate(iframes):
            all_frames.append(frame)
            
        print(f"DOM 树嗅探完毕：主页面共包含 {len(all_frames)-1} 个潜藏数据框架槽，开始穿透探测...")

        # 挨个进入框架尝试清洗数据
        for current_frame in all_frames:
            try:
                if current_frame != "main_page":
                    driver.switch_to.frame(current_frame)
                
                # 寻找带有卡片特质的所有元素
                cards = driver.find_elements(By.CSS_SELECTOR, ".card, .panel, [class*='card'], [style*='border']")
                
                # 兜底：如果类名被完全抹除，直接寻找带有“复制”属性的独立父级块
                if not cards:
                    cards = driver.find_elements(By.XPATH, "//*[contains(text(), '复制')]/ancestor::div[position()<=3]")
                
                for card in cards:
                    card_text = card.text
                    if not card_text:
                        continue
                    
                    # 精准过滤：这一块里必须写着“正常”，且彻底排除“异常”与“锁定”
                    if "正常" in card_text:
                        if "异常" in card_text or "锁定" in card_text:
                            continue
                        
                        # 1. 正则锁定账号邮箱
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', card_text)
                        if not email_match:
                            continue
                        username = email_match.group(0).strip()
                        
                        # 2. 挖掘隐藏在复制按钮属性内的密码
                        password = ""
                        buttons = card.find_elements(By.CSS_SELECTOR, "button, .btn, a, [data-clipboard-text]")
                        for btn in buttons:
                            val = btn.get_attribute("data-clipboard-text") or btn.get_attribute("data-text")
                            if val:
                                val = val.strip()
                                # 只要属性值和账号邮箱不同，说明就是密码
                                if val != username and "@" not in val and len(val) >= 4:
                                    password = val
                                    break
                        
                        # 3. 兜底清洗：如果属性里没抓到，说明直接以文本平铺在里面，直接打碎文本匹配
                        if not password:
                            parts = [p.strip() for p in re.split(r'[\s|｜,，;；\t:]+', card_text)]
                            for part in parts:
                                if part != username and len(part) >= 5:
                                    if not re.search(r'[\u4e00-\u9fa5]', part) and "@" not in part and "202" not in part:
                                        password = part
                                        break
                                        
                        if username and password:
                            res = (f"👤 账号：`{escape_markdown(username)}`\n"
                                   f"🔑 密码：`{escape_markdown(password)}`")
                            
                            if res not in account_data:
                                account_data.append(res)
                                print(f"🎉【过滤通过】穿透捕获成功 -> 账号: {username} | 密码: {password}")
            except Exception as frame_e:
                pass
            finally:
                # 每次执行完，无论成功与否，必须切回主页面根节点
                driver.switch_to.default_content()

        driver.quit()
        return account_data

    except Exception as e:
        print(f"❌ 链路收割器崩溃: {e}")
        try: driver.quit()
        except: pass
        return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
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
        f"❤️ *欢迎关注我们交流群：*@{escape_markdown('bh888')}\n"
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
    print(f"TG 推送完成，状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
