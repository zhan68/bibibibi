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
        
        # 💡 等待加载：直到含有 waves-effect 类的按钮渲染就位
        wait = WebDriverWait(driver, 25)
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "waves-effect")))
        
        # 留出 4 秒给异步数据平铺完毕
        time.sleep(4)
        
        # 💡 定位包含了单个卡片所有的 col 容器大方块
        cards = driver.find_elements(By.CSS_SELECTOR, "#apple > div[class*='col'], #apple > div")
        
        print(f"[通道 6] 成功锁定 {len(cards)} 个独立账号卡片方块，开始提取...")
        
        account_data = []
        
        for idx, card in enumerate(cards):
            try:
                card_text = card.text
                if not card_text or "@" not in card_text:
                    continue 

                # 1. 地区提取：直接抓取右侧写死的文本
                region = "美区账号"
                try:
                    region_element = card.find_element(By.CSS_SELECTOR, ".float-end")
                    if region_element:
                        raw_region = region_element.text.strip()
                        if raw_region: region = raw_region
                except:
                    if "美国" in card_text: region = "美国"
                    elif "越南" in card_text: region = "越南"
                    elif "香港" in card_text: region = "中国香港"

                # 2. 账号与密码精准轰炸：锁定内部的 waves-effect 按钮
                btns = card.find_elements(By.CLASS_NAME, "waves-effect")
                
                if len(btns) >= 2:
                    # 💥 破局核心：直接抓取网页真正的属性 data-copy！
                    username = btns[0].get_attribute("data-copy")
                    password = btns[1].get_attribute("data-copy")
                    
                    if username: username = username.strip()
                    if password: password = password.strip()

                    # 3. 数据有效性清算与格式组装
                    if username and password and "@" in username and "@" not in password:
                        res = (f"📍 地区：{escape_markdown(region)}\n"
                               f"👤 账号：`{escape_markdown(username)}`\n"
                               f"🔑 密码：`{escape_markdown(password)}`")
                        
                        if res not in account_data:
                            account_data.append(res)
                            print(f"🥇 [通道 6] 提纯成功 -> 地区: {region} | 账号: {username} | 密码: {password}")
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
        print("⚠️ [通道 6] 最终提纯出的列表为空，取消本次 TG 推送。")
        return

    print(f"🎉 [通道 6] 成功抓取到 {len(content_list)} 组账号，正在向 TG 推送最新大帖...")
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    # 📌 满血对齐广告格式
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
    print(f"[通道 6] TG 大图大贴连发完成，状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
