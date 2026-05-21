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
    
    # 💡 核心自愈补丁：直接锁定系统原生 Chrome 路径
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument('--headless=new')             
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')               
    
    # 高级伪装
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--lang=zh-CN,zh;q=0.9')
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
            print("[通道 2] 密码已提交，等待页面完整加载...")
            time.sleep(12) # 留出充足时间让所有卡片完全解密出来
        except Exception as e:
            print(f"[通道 2] 密码环节处理异常: {e}")

        # --- 2. 【全新大招】容器级切片解析，完美解决多号漏号问题 ---
        print("[通道 2] 开始执行大卡片外壳深度嗅探...")
        
        # 寻找页面上包裹账号密码的所有独立卡片外壳
        cards = driver.find_elements(By.CSS_SELECTOR, "div[class*='card'], div[class*='panel'], div[style*='border'], .layui-card")
        
        # 兜底：如果没捞到，就利用特征明显的“复制账号”字样向上逆向寻找父级容器
        if not cards:
            cards = driver.find_elements(By.XPATH, "//*[contains(text(), '账号') or contains(text(), '帐号')]/ancestor::div[position()<=3]")
            
        print(f"[通道 2] 成功锁定了 {len(cards)} 个独立账号数据外壳容器，开始逐个穿透提纯...")
        
        account_data = []
        
        for idx, card in enumerate(cards):
            try:
                card_text = card.text
                if not card_text or "@" not in card_text:
                    continue # 如果方块里连邮箱特征都没有，直接跳过
                
                # A. 提取卡片内的区域标志（如中国大陆、美国）
                region = "共享账号"
                if "中国" in card_text: region = "中国大陆"
                elif "美国" in card_text or "美" in card_text: region = "美国"
                elif "香港" in card_text: region = "中国香港"
                
                # B. 正则高精度榨取邮箱账号
                email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', card_text)
                if not email_match:
                    continue
                username = email_match.group(0).strip()
                
                # C. 深度挖掘隐藏密码
                password = ""
                # 优先去捞卡片内部所有带复制特性的按钮属性
                crypto_elements = card.find_elements(By.CSS_SELECTOR, "button, a, [data-clipboard-text]")
                for elem in crypto_elements:
                    val = elem.get_attribute("data-clipboard-text") or elem.get_attribute("data-text")
                    if val:
                        val = val.strip()
                        if val != username and "@" not in val and len(val) >= 4 and "*" not in val:
                            password = val
                            break
                            
                # 兜底：如果属性里被混淆了，直接打碎卡片内的纯文本，精准剔除账号、时间后拿到密码
                if not password:
                    lines = [line.strip() for line in card_text.split("\n") if line.strip()]
                    for line in lines:
                        if line != username and not any(k in line for k in ["上次检查", "202", "正常", "锁定", "复制", "中国", "美国"]):
                            # 剔除掉中文提示后，剩下的纯英数英符组合即为密码
                            clean_line = re.sub(r'[\u4e00-\u9fa5\s:]', '', line)
                            if len(clean_line) >= 4 and "@" not in clean_line and "*" not in clean_line:
                                password = clean_line
                                break
                
                # D. 有效性终审并打包
                if username and password:
                    res = (f"📍 地区：{escape_markdown(region)}\n"
                           f"👤 账号：`{escape_markdown(username)}`\n"
                           f"🔑 密码：`{escape_markdown(password)}`")
                    if res not in account_data:
                        account_data.append(res)
                        print(f"🥇 [通道 2] 容器 {idx+1} 提取成功 -> 地区: {region} | 账号: {username}")
            except Exception as card_e:
                print(f"⚠️ [通道 2] 解析单个卡片容器时跳过: {card_e}")
                continue
        
        driver.quit()
        return account_data

    except Exception as e:
        print(f"❌ [通道 2] 抓取过程总体崩溃: {e}")
        try: driver.quit()
        except: pass
        return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not content_list: 
        print("⚠️ [通道 2] 未获取到有效数据，取消本次 TG 推送。")
        return

    print(f"🎉 [通道 2] 成功抓取到 {len(content_list)} 组账号，正在向 TG 推送最新大帖...")
    
    header = "🚀 *最新 Apple ID 共享更新【2】*"
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
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    media_group = [{'type': 'photo', 'media': img_url, 'caption': full_caption, 'parse_mode': 'MarkdownV2'}]
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    
    res = requests.post(url, data={"chat_id": chat_id, "media": json.dumps(media_group)})
    if res.status_code == 200:
        print("🎉 [通道 2] 多账号大贴发布成功！")
    else:
        print(f"❌ [通道 2] 发布失败: {res.text}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
