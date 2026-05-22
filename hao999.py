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
    
    # [span_1](start_span)🎯【完美修复】将导致崩溃的 add_user_agent 修正为标准的 add_argument 注入[span_1](end_span)
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
        except Exception:
            print("[通道 5] 页面到达硬性载入边界，开始强制提取当前 DOM 缓存 data...")
            
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
                    card_html = card.get_attribute("innerHTML")
                    card_text = card.text
                    if not card_html or not card_text:
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
                        
                        # 💡 2. 【高精度地区修复】改用底层 innerHTML 源码扫描，防止“美国、中国大陆”等汉字被过滤或隐藏
                        region = "美国" # 默认美区兜底
                        if "中国" in card_html or "大陆" in card_html:
                            region = "中国大陆"
                        elif "香港" in card_html:
                            region = "中国香港"
                        elif "台湾" in card_html:
                            region = "中国台湾"
                        elif "越南" in card_html:
                            region = "越南"
                        
                        # 3. 挖掘隐藏在复制按钮属性内的密码
                        password = ""
                        buttons = card.find_elements(By.CSS_SELECTOR, "button, .btn, a, [data-clipboard-text]")
                        for btn in buttons:
                            val = btn.get_attribute("data-clipboard-text") or btn.get_attribute("data-text")
                            if val:
                                val = val.strip()
                                # 🎯【核心去Bug锁】放开对密码包含 @ 的安全误杀，只要不以常见域名结尾就属于合法密码！
                                if val != username and len(val) >= 4 and not any(k in val for k in [".com", ".net", ".org", ".cl"]):
                                    password = val
                                    break
                        
                        # 4. 兜底清洗：如果属性里没抓到，说明直接以文本平铺在里面，直接打碎文本匹配
                        if not password:
                            parts = [p.strip() for p in re.split(r'[\s|｜,，;；\t:]+', card_text) if p.strip()]
                            for part in parts:
                                if part != username and len(part) >= 4:
                                    # 剥离掉干扰汉字后，如果剩下的非域名密文长度足够，直接放行（支持带 @ 的密码）
                                    if not re.search(r'[\u4e00-\u9fa5]', part) and "202" not in part and not any(k in part for k in [".com", ".net", ".org", ".cl"]):
                                        password = part
                                        break
                                        
                        if username and password:
                            # 精美编织带地区的卡片主体
                            res = (f"📍 地区：{escape_markdown(region)}\n"
                                   f"👤 账号：`{escape_markdown(username)}`\n"
                                   f"🔑 密码：`{escape_markdown(password)}`")
                            
                            if res not in account_data:
                                account_data.append(res)
                                print(f"🎉【过滤通过】穿透捕获成功 -> 地区: {region} | 账号: {username} | 密码: {password}")
            except Exception:
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
    
    # 💡 核心闭合：空号时只打印关键字，将广播通报权交还给 123.py 主大脑，绝不提前发生数据掐架截断
    if not content_list: 
        print("⚠️ [通道 5] 未获取到有效数据，取消本次 TG 推送。")
        return

    print(f"🎉 [通道 5] 成功抓取到 {len(content_list)} 组账号，正在组织完美多号排版向 TG 推送...")
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    # 1. 标题加粗
    header = "🚀 *最新 Apple ID 共享更新【5】*"
    
    # 2. 账号主体（完美用分割线拼接所有人）
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
    
    # 组合最终大 Caption 外壳
    full_caption = f"{header}\n{body}\n\n{time_str}\n{warning_str}\n\n{notice_str}\n\n{follow_str}\n{service_str}"
    
    # 💡 完美应用 MediaGroup 架构，强力兼容多账号超长文本，永不吞号！
    media_group = [
        {
            'type': 'photo',
            'media': img_url,
            'caption': full_caption,
            'parse_mode': 'MarkdownV2'
        }
    ]

    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    res = requests.post(url, json={"chat_id": chat_id, "media": json.dumps(media_group)})
    print(f"[通道 5] TG 多号大贴连发完成，状态码: {res.status_code}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram(data)
