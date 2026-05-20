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
    
    print(f"开始使用 Playwright 访问页面: {target_url}")
    
    with sync_playwright() as p:
        # 启动 Chromium 浏览器，模拟现代浏览器防止被文档系统拦截
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = context.new_page()
        
        try:
            # 访问页面，等待网络空闲
            page.goto(target_url, wait_until="networkidle")
            print("页面初步加载完成，等待数据解密渲染 (10秒)...")
            page.wait_for_timeout(10000) # 强力等待10秒
            
            # --- 核心黑科技：多重定位策略 ---
            # 1. 尝试直接捞取所有的文本块，按文档流聚合数据
            print("正在深度解析页面节点文本...")
            
            # 使用 Playwright 强大的定位器，抓取页面上所有看似表格行或段落的文本
            # 兼容 <tr>、具有 row 属性的 div、甚至普通的 p 标签
            elements = page.locator('tr, .row, .grid-row, p, div[class*="line"], div[class*="row"]').all()
            print(f"扫描到可能包含数据的节点共: {len(elements)} 个")
            
            for element in elements:
                try:
                    line_text = element.inner_text()
                    if not line_text:
                        continue
                        
                    # 清理换行，将同一块（或同一行表格）的数据强行用“ | ”拼起来
                    clean_line = " | ".join([part.strip() for part in line_text.split("\n") if part.strip()])
                    
                    # 只要包含“正常”或者“状态正常”，就启动提取
                    if "正常" in clean_line:
                        print(f"发现有效状态行 -> {clean_line}")
                        
                        # 使用宽松的正则表达式匹配邮箱账号
                        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', clean_line)
                        
                        if email_match:
                            username = email_match.group(0)
                            password = ""
                            
                            # 将这行文本切开，找密码
                            parts = [p.strip() for p in re.split(r'[\s|｜,，;；\t:]+', clean_line)]
                            for part in parts:
                                if part == username or not part:
                                    continue
                                # 密码过滤特征：无中文，无@，无网址，长度在5-22位之间
                                if not re.search(r'[\u4e00-\u9fa5]', part) and "@" not in part and "http" not in part:
                                    if 5 <= len(part) <= 22 and part not in ["正常", "状态正常"]:
                                        password = part
                                        break
                            
                            if username and password:
                                res = (f"📍 地区：{escape_markdown('源2-共享')}\n"
                                       f"👤 账号：`{escape_markdown(username)}`\n"
                                       f"🔑 密码：`{escape_markdown(password)}`")
                                
                                if res not in account_data:
                                    account_data.append(res)
                                    print(f"🎉【抓取成功】提取到有效 ID: {username}")
                except Exception as row_err:
                    continue # 容错，防止单行结构异常卡死整个循环
                    
            # 2. 如果多重定位器完全没有抓到，使用终极兜底策略：全页面模糊查找
            if not account_data:
                print("⚠️ 定位器未能精准切分数据，启动全页纯文本深度模糊搜索...")
                full_text = page.evaluate("() => document.body.innerText")
                all_emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', full_text)
                
                # 模糊将所有有 @ 符号的行打印在日志里，方便你下次排查
                print(f"全页发现的所有邮箱账号: {all_emails}")
                
            browser.close()
            return account_data

        except Exception as e:
            print(f"Playwright 运行崩溃: {e}")
            try:
                page.screenshot(path="error_debug.png")
            except:
                pass
            browser.close()
            return None

def send_to_telegram(content_list):
    token = os.environ.get('BOT_TOKEN')
    chat_id = "@yinlianID"
    if not content_list: 
        print("没有获取到有效账号，取消发送。")
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
