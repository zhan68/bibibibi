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

def escape_markdown(text):
    """转义 Telegram MarkdownV2 特殊字符"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_apple_ids():
    chrome_options = Options()
    
    # 💡 核心自愈补丁：直接锁定系统原生 Chrome 路径
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument('--headless=new')             
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')               
    chrome_options.add_argument('--window-size=1440,900')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    chrome_options.add_argument('--lang=zh-CN,zh;q=0.9')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false') 

    try:
        print("🚀 [通道 5] 正在直接调动系统原生 Chrome 驱动开跑...")
        driver = webdriver.Chrome(options=chrome_options)
        
        driver.set_page_load_timeout(25)
        driver.set_script_timeout(25)
        
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"[通道 5] 开始访问页面: {target_url}")
        
        try:
            driver.get(target_url)
        except Exception:
            print("[通道 5] 页面到达硬性载入边界，开始强制提取当前 DOM 缓存数据...")
            
        time.sleep(8)
        account_data = []
        
        all_frames = ["main_page"]
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for idx, frame in enumerate(iframes):
            all_frames.append(frame)
            
        print(f"[通道 5] DOM 树嗅探完毕：主页面共包含 {len(all_frames)-1} 个潜藏数据框架槽，开始穿透探测...")

        for current_frame in all_frames:
            try:
                if current_frame != "main_page":
                    driver.switch_to.frame(current_frame)
                
                cards = driver.find_elements(By.CSS_SELECTOR, ".card, .panel, [class*='card'], [style*='border']")
                if not cards:
                    cards = driver.find_elements(By.XPATH, "//*[contains(text(), '复制')]/ancestor::div[position()<=3]")
                
                for card in cards:
                    card_text = card.text
                    if not card_text:
                        continue
                    
                    if "正常" in card_text:
                        if "异常" in card_text or "锁定" in card_text:
                            continue
                        
                        # 1. 账号邮箱正则提取
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', card_text)
                        if not email_match:
                            continue
                        username = email_match.group(0).strip()
                        
                        # 💡 2. 国家地区自动动态分析
                        region = "共享账号"
                        if "美国" in card_text: region = "美国"
                        elif "中国" in card_text or "大陆" in card_text: region = "中国大陆"
                        elif "香港" in card_text: region = "中国香港"
                        elif "台湾" in card_text: region = "中国台湾"
                        
                        # 3. 密码按钮内部属性探测
                        password = ""
                        buttons = card.find_elements(By.CSS_SELECTOR, "button, .btn, a, [data-clipboard-text]")
                        for btn in buttons:
                            val = btn.get_attribute("data-clipboard-text") or btn.get_attribute("data-text")
                            if val:
                                val = val.strip()
                                # 只要这个属性不等于邮箱，且长度足够，放行带有 @ 的合法密码
                                if val != username and len(val) >= 4 and not any(k in val for k in [".com", ".net", ".org", ".cl"]):
                                    password = val
                                    break
                        
                        # 4. 文本打碎兜底清洗
                        if not password:
                            parts = [p.strip() for p in re.split(r'[\s|｜,，;；\t:]+', card_text) if p.strip()]
                            for part in parts:
                                if part != username and len(part) >= 4:
                                    # 💥 降维打破：放宽对密码包含 @ 的安全过滤，只要不以常见邮箱域名结尾即可放行！
                                    if not re.search(r'[\u4e00-\u9fa5]', part) and "202" not in part and not any(k in part for k in [".com", ".net", ".org", ".cl"]):
                                        password = part
                                        break
                                        
                        if username and password:
                            # 将国家和账号数据精美织入
                            res = (f"📍 地区：{escape_markdown(region)}\n"
                                   f"👤 账号：`{escape_markdown(username)}`\n"
                                   f"🔑 密码：`{escape_markdown(password)}`")
                            
                            if res not in account_data:
                                account_data.append(res)
                                print(f"🎉【过滤通过】穿透捕获成功 -> 地区: {region} | 账号: {username} | 密码: {password}")
            except:
                pass
            finally:
                driver.switch_to.default_content()

        driver.quit()
        return account_data

    except Exception as e:
        print(f"❌ [通道 5] 链路收割器崩溃: {e}")
        try: driver.quit()
        except: pass
        return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not token: return
    
    if not content_list: 
        print("⚠️ [通道 5] 未获取到有效数据，取消本次 TG 推送。")
        return

    print(f"🎉 [通道 5] 成功抓取到 {len(content_list)} 组账号，正在组织完美多号排版向 TG 推送...")
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    header = "🚀 *最新 Apple ID 共享更新【5】*"
    body = "\n\n" + "\n\n──────────────\n\n".join(content_list)
    
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    time_str = f"🕒 更新时间：{escape_markdown(bj_time)}"
    warning_str = f"⚠️ *{escape_markdown('警告：严禁在设置/iCloud中登录！')}*"
    
    notice_val = "共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待15分钟更新，请谅解"
    notice_str = f"*{escape_markdown(notice_val)}*"
    follow_str = f"❤️ *{escape_markdown('欢迎关注我们交流群：')}*@bh888"
    service_str = f"            *{escape_markdown('客    服：')}*@zzyyy"
    
    full_caption = f"{header}\n{body}\n\n{time_str}\n{warning_str}\n\n{notice_str}\n\n{follow_str}\n{service_str}"
    
    media_group = [{'type': 'photo', 'media': img_url, 'caption': full_caption, 'parse_mode': 'MarkdownV2'}]
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    
    res = requests.post(url, json={"chat_id": chat_id, "media": json.dumps(media_group)})
    print(f"[通道 5] TG 多号大贴连发完成，状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
