import os
import requests
import time
import re
import json
from datetime import datetime, timedelta, timezone
from selenium import webdriver
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
    
    # 💡 核心自愈补丁：锁定 Docker 容器内部官方 Chrome 路径，彻底丢弃 DriverManager
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument('--headless=new')             # 无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')               # 禁用 GPU 防止 Linux 容器内卡死
    chrome_options.add_argument('--lang=zh-CN,zh;q=0.9')
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')

    try:
        print("🚀 [通道 6] 正在直接调动系统原生 Chrome 驱动开跑...")
        driver = webdriver.Chrome(options=chrome_options)
        
        target_url = "https://proxy4all.github.io/FreeShadowrocket/"
        print(f"[通道 6] 开始访问页面: {target_url}")
        driver.get(target_url)
        
        # 💡 等待加载：直到转圈的 loading 元素消失，且账号按钮加载就位
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "waves-effect")))
        
        # 留出 3 秒给数据渲染完整
        time.sleep(3)
        
        # 💡 【容器级精准穿透】直接锁定 id="apple" 下面的所有独立卡片方块
        cards = driver.find_elements(By.CSS_SELECTOR, "#apple > div.col-12, #apple > div[class*='col']")
        
        # 兜底：如果类名变动，直接抓取包含 waves-effect 的父级卡片
        if not cards:
            cards = driver.find_elements(By.XPATH, "//*[contains(@class, 'waves-effect')]/ancestor::div[contains(@class, 'card') or position()<=2]")

        print(f"[通道 6] 成功锁定 {len(cards)} 个独立账号卡片方块，开始精准提纯...")
        
        account_data = []
        
        for idx, card in enumerate(cards):
            try:
                card_text = card.text
                if not card_text or "@" not in card_text:
                    continue # 如果方块里没有邮箱，直接跳过
                
                # 🎯 A. 精准提取卡片内部写死的地区文本（如：“美国”）
                region = "美区账号" # 默认兜底
                try:
                    # 寻找带 float-end 或者带有地区图标旁边的文本
                    region_element = card.find_element(By.CSS_SELECTOR, ".float-end, i[class*='fi'] + span, i[class*='fi']")
                    if region_element:
                        raw_region = region_element.text.strip()
                        if raw_region:
                            region = raw_region
                except:
                    # 兜底正则：如果在卡片纯文本里看到了中文，提取出来
                    if "美国" in card_text: region = "美国"
                    elif "香港" in card_text: region = "中国香港"
                    elif "大陆" in card_text or "中国" in card_text: region = "中国大陆"

                # B. 精准提取卡片内部的账号和密码按钮
                btns = card.find_elements(By.CLASS_NAME, "waves-effect")
                if len(btns) >= 2:
                    # 第一个按钮是账号，优先拿真实复制属性，拿不到拿文本
                    username = btns[0].get_attribute("data-clipboard-text") or btns[0].text.strip()
                    # 第二个按钮是密码
                    password = btns[1].get_attribute("data-clipboard-text") or btns[1].text.strip()
                    
                    # 强力清洗邮箱
                    if "@" in username and len(password) >= 4 and "@" not in password:
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', username)
                        if email_match:
                            clean_username = email_match.group(0).strip()
                            
                            res = (f"📍 地区：{escape_markdown(region)}\n"
                                   f"👤 账号：`{escape_markdown(clean_username)}`\n"
                                   f"🔑 密码：`{escape_markdown(password)}`")
                            
                            if res not in account_data:
                                account_data.append(res)
                                print(f"🥇 [通道 6] 卡片 {idx+1} 提取成功 -> 地区: {region} | 账号: {clean_username}")
            except Exception as card_e:
                continue

        driver.quit()
        return account_data

    except Exception as e:
        print(f"❌ [通道 6] 链路收割器崩溃: {e}")
        try: driver.quit()
        except: pass
        return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not token: return
    
    if not content_list: 
        print("⚠️ [通道 6] 未获取到有效数据，取消本次 TG 推送。")
        return

    print(f"🎉 [通道 6] 成功抓取到 {len(content_list)} 组账号，正在向 TG 推送最新大帖...")
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    # 📌 完美对齐你的官方频道大图排版格式
    header = "🚀 *最新 Apple ID 共享更新【6】*"
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
    print(f"[通道 6] TG 大图大贴发送完成，状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
