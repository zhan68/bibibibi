import os
import requests
import time
import re
from datetime import datetime, timedelta, timezone
from playwright.sync_api import sync_playwright

def escape_markdown(text):
    """转义 Telegram MarkdownV2 特殊字符"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_apple_ids():
    target_url = "https://doc.bat520.cc/doc/8/"
    account_data = []
    
    print(f"开始使用 Playwright 访问知识库页面: {target_url}")
    
    with sync_playwright() as p:
        # 启动 Chromium，配置标准的桌面分辨率
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # 访问页面，设定 30 秒超时，等待网络状态基本空闲
            page.goto(target_url, wait_until="domcontentloaded", timeout=30000)
            print("基础页面已载入，深度等待动态组件及内置 iframe 异步解密 (12秒)...")
            page.wait_for_timeout(12000)
            
            # --- 核心黑科技：跨越 iframe 与沙箱的全局属性捕获器 ---
            # 不论数据在当前页面还是嵌套在 iframe 里，直接全自动化检索带有 @ 符号且包含复制特征的属性明文
            print("正在扫描全局 DOM 树，提取加密数据属性...")
            
            # 策略 1：利用 Playwright 的全包裹器，嗅探所有隐藏了 data-clipboard-text 属性的节点
            elements = page.locator("[data-clipboard-text]").all()
            print(f"全局嗅探完毕：共捕获到绑有明文数据的节点: {len(elements)} 个")
            
            raw_pairs = []
            for el in elements:
                try:
                    text_val = el.get_attribute("data-clipboard-text")
                    if text_val:
                        raw_pairs.append(text_val.strip())
                except:
                    continue
            
            # 策略 2：如果策略 1 拿到的节点很少，说明在 iframe 内部，直接穿透所有的 Frames 进行搜刮
            if len(raw_pairs) < 2:
                print("触发跨域穿透防御：正在深度收割嵌套框架(Frames)内的隐藏属性...")
                for frame in page.frames:
                    try:
                        frame_elements = frame.locator("[data-clipboard-text]").all()
                        for fe in frame_elements:
                            val = fe.get_attribute("data-clipboard-text")
                            if val and val.strip() not in raw_pairs:
                                raw_pairs.append(val.strip())
                    except:
                        continue
                        
            print(f"明文池数据构建成功，总计捞出原生字段 {len(raw_pairs)} 个。开始双向对齐洗数据...")
            
            # --- 智能洗数据与状态对齐算法 ---
            # 提取所有邮箱账号
            emails = [item for item in raw_pairs if "@" in item and "." in item and "http" not in item.lower()]
            # 提取潜在的密码
            passwords = [item for item in raw_pairs if item not in emails and len(item) >= 4 and not re.search(r'[\u4e00-\u9fa5]', item)]
            
            # 此时我们需要过滤“状态正常”的卡片，利用页面内容全平铺文本检测法进行二次校验
            # 完美避开因为缺少中文字体而导致的死锁，只读取纯字符串
            full_visible_text = page.evaluate("() => document.body.innerText")
            for frame in page.frames:
                try: full_visible_text += "\n" + frame.evaluate("() => document.body.innerText")
                except: pass
                
            # 清理换行干扰
            flat_text = " ".join(full_visible_text.split())
            
            # 开始成对组装账号密码
            for i in range(min(len(emails), len(passwords))):
                username = emails[i]
                password = passwords[i]
                
                # 核心状态过滤锁：只有当这个账号在页面全局文本中紧邻的上下文中不含有“异常”、“锁定”字样才保留
                # 如果这个账号附近有“异常”或者没有“正常”，则视为坏号过滤掉
                account_zone_match = re.search(rf"{re.escape(username)}.*?(异常|锁定|正常|状态正常)", flat_text)
                
                is_status_ok = True
                if account_zone_match:
                    status_word = account_zone_match.group(1)
                    if status_word in ["异常", "锁定"]:
                        is_status_ok = False
                        print(f"❌ [已被拦截] 账号 {username} 检测到状态为异常，跳过推送")
                
                if is_status_ok:
                    res = (f"👤 账号：`{escape_markdown(username)}`\n"
                           f"🔑 密码：`{escape_markdown(password)}`")
                    
                    if res not in account_data:
                        account_data.append(res)
                        print(f"🎉【过滤通过】账号: {username} | 密码: {password}")
                        
            browser.close()
            return account_data

        except Exception as e:
            print(f"❌ Playwright 核心动力链运行崩溃: {e}")
            try: browser.close()
            except: pass
            return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
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
        f"❤️ *欢迎关注我们频道：*@{escape_markdown('yinlianID')}\n"
        f"            *客    服：*@{escape_markdown('zzyyy')}"
    )
    
    header = "🚀 *最新 Apple ID 共享更新【3】*"
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
