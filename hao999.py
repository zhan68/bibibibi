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
    
    # 💡 核心自愈补丁：直接锁定系统原生 Chrome 路径，彻底丢弃饱含 Bug 的 DriverManager
    chrome_options.binary_location = "/usr/bin/google-chrome"
    chrome_options.add_argument('--headless=new')             # 使用推荐的全新无头模式
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-gpu')               # 禁用 GPU 防止 Linux 容器内卡死
    chrome_options.add_argument('--window-size=1440,900')
    
    # 💡 反爬虫高级伪装参数
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36')
    
    # 强行给 headless 浏览器注入字体，防止乱码导致 JS 解密挂起
    chrome_options.add_argument('--lang=zh-CN,zh;q=0.9')
    chrome_options.add_argument('--blink-settings=imagesEnabled=false') # 禁用图片，极大加快加载速度

    try:
        print("🚀 [通道 5] 正在直接调动系统原生 Chrome 驱动开跑...")
        driver = webdriver.Chrome(options=chrome_options)
        
        # 设置 25 秒强制超时，绝不在 Actions 中死锁
        driver.set_page_load_timeout(25)
        driver.set_script_timeout(25)
        
        target_url = "https://doc.bat520.cc/doc/8/"
        print(f"[通道 5] 开始访问页面: {target_url}")
        
        try:
            driver.get(target_url)
        except Exception as load_e:
            print("[通道 5] 页面到达硬性载入边界，开始强制提取当前 DOM 缓存数据...")
            
        # 静默等待 8 秒，给动态框架充足的渲染时间
        time.sleep(8)
        
        account_data = []
        
        # 探测全页面所有的框架上下文（穿透内置 iframe 容器）
        all_frames = ["main_page"]
        iframes = driver.find_elements(By.TAG_NAME, "iframe")
        for idx, frame in enumerate(iframes):
            all_frames.append(frame)
            
        print(f"[通道 5] DOM 树嗅探完毕：主页面共包含 {len(all_frames)-1} 个潜藏数据框架槽，开始穿透探测...")

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
        print(f"❌ [通道 5] 链路收割器崩溃: {e}")
        try: driver.quit()
        except: pass
        return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not token: return
    
    # 💡 核心对齐升级：若未读取到任何有效活号，向频道通报报平安，不再死气沉沉静默
    if not content_list: 
        print("[通道 5] 没有读取到任何[状态正常]的有效账号，发送空号平安通知...")
        header = "🚀 *最新 Apple ID 共享更新提示*"
        status_str = "📍 状态：🔴 *当前暂无可用的活号*"
        body = f"📋 *通知提醒：*\n经系统实时动态监测，当前 *【通道 5】* 目标网站线上的所有共享 ID 已经全部处于锁定维护或异常状态，本次轮询未获取到有效活号。"
        hint = "请大家稍安勿躁，请耐心等待下一轮自动轮询更新，感谢理解！"
        
        tz_bj = timezone(timedelta(hours=8))
        bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
        
        full_text = (
            f"{header}\n\n{status_str}\n\n{body}\n\n"
            f"*{escape_markdown(hint)}*\n\n──────────────\n\n"
            f"🕒 监测时间：{escape_markdown(bj_time)}\n"
            f"❤️ *{escape_markdown('欢迎关注我们交流群：')}*@bh888\n"
            f"            *{escape_markdown('客    服：')}*@zzyyy"
        )
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": full_text, "parse_mode": "MarkdownV2"})
        return

    print(f"🎉 [通道 5] 成功抓取到 {len(content_list)} 组账号，正在组织完美多号排版向 TG 推送...")
    
    # 1. 标题加粗
    header = "🚀 *最新 Apple ID 共享更新【5】*"
    
    # 2. 账号主体
    body = "\n\n" + "\n\n──────────────\n\n".join(content_list)
    
    # 3. 时间与警告
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    time_str = f"🕒 更新时间：{escape_markdown(bj_time)}"
    warning_str = f"⚠️ *{escape_markdown('警告：严禁在设置/iCloud中登录！')}*"
    
    # 4. 公告与客服
    notice_val = "共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待15分钟更新，请谅解"
    notice_str = f"*{escape_markdown(notice_val)}*"
    follow_str = f"❤️ *{escape_markdown('欢迎关注我们交流群：')}*@bh888"
    service_str = f"            *{escape_markdown('客    服：')}*@zzyyy"
    
    # 组合最终 Caption
    full_caption = f"{header}\n{body}\n\n{time_str}\n{warning_str}\n\n{notice_str}\n\n{follow_str}\n{service_str}"
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    # 💡 完美应用 MediaGroup 架构，强力兼容多账号超长文本，永不发生格式覆盖和吞号 Bug！
    media_group = [
        {
            'type': 'photo',
            'media': img_url,
            'caption': full_caption,
            'parse_mode': 'MarkdownV2'
        }
    ]

    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    payload = {
        "chat_id": chat_id,
        "media": json.dumps(media_group)
    }
    
    res = requests.post(url, json=payload)
    print(f"[通道 5] TG 推送完成，状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
