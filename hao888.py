import os
import sys
import subprocess
import requests
import time
import re
import json
from datetime import datetime, timedelta, timezone

# ==========================================
# 💡 核心破局补丁：强行与 123.py 保持绝对一致，重定向浏览器下载路径到当前可写目录
# ==========================================
os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.join(os.getcwd(), ".local-browsers")

def auto_fix_render_env():
    """纯代码外挂：无需配置后台，hao888 启动时自己独立安装环境与本地内核"""
    print("=== [Render 独立沙盒环境全自动自愈启动] ===")
    
    # 1. 独立安装完美兼容 Python 3.9 的 playwright 动态库（不干扰其他通道的 Selenium）
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("未检测到 playwright 核心库，正在独立配置当前通道运行时环境...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright==1.44.0"])

    # 2. 强行下载防爬 Chromium 浏览器内核到项目本地可写文件夹
    try:
        print("正在向本地可写目录下载防爬 Chromium 内核...")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("🎉 [环境热装载完成] 专属本地浏览器内核已完美就位！")
    except Exception as e:
        print(f"-> 下载内核提示（可能已存在）: {str(e)}")
    print("=========================================\n")

# 在程序启动的第 0 秒，直接肉搏修复环境，确保 123.py 子进程不卡死
auto_fix_render_env()

# 环境自愈完成后，正式引入 Playwright 组件开始干活
from playwright.sync_api import sync_playwright

def escape_markdown(text):
    """转义 Telegram MarkdownV2 特殊字符，防止由于格式符号导致拒收"""
    escape_chars = r'_[]()~>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def clean_chinese_email(raw_text):
    """强力过滤变动中文：不管怎么混淆插眼，100% 榨取出中间的纯正邮箱账号"""
    if not raw_text or "@" not in raw_text:
        return None
    # 1. 刮掉所有的中文字符以及中文标点
    no_chinese = re.sub(r'[\u4e00-\u9fa5\u3000-\u303f\uff00-\uffef]', '', raw_text)
    # 2. 刮掉可能带有的一切多余空格、换行
    no_chinese = re.sub(r'\s+', '', no_chinese)
    # 3. 精准捞出纯邮箱
    email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', no_chinese)
    if email_match:
        return email_match.group(0).strip()
    return None

def get_apple_ids():
    """Playwright 专属高级防风控卡片及网页内存函数拦截器"""
    account_data = []
    
    with sync_playwright() as p:
        print("正在启动防爬无头浏览器进程...")
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4.1 Mobile/15E148 Safari/604.1",
            viewport={"width": 390, "height": 844},
            is_mobile=True,
            has_touch=True
        )
        
        page = context.new_page()
        print("正在安全连接访问目标网站...")
        
        try:
            page.goto("https://idshare001.me/goso.html", timeout=45000, wait_until="domcontentloaded")
            time.sleep(3)
            
            # --- 1. 精准破防网页弹出的密码验证墙 ---
            print("发现密码验证墙，启动自动输入破防逻辑...")
            pwd_input = page.locator("//input[@type='text' or @type='password'] | //input").first
            pwd_input.fill("禁止登陆设置否则会被坏人锁机")
            time.sleep(1)
            
            # 直接按下物理回车键触发表单进入
            pwd_input.press("Enter")
            print("密码验证码回车提交完毕，正在跨入内部卡片页...")
            time.sleep(6)
        except Exception as e:
            print(f"前置验证墙处理异常或已被前置跳过: {str(e)}")

        # --- 2. 【核心破局大招】注入内存级外挂：劫持重写网页的底层复制函数 ---
        print("正在向网页注入内存拦截钩子...")
        page.evaluate("""() => {
            window._lastCopiedText = "";
            navigator.clipboard.writeText = async (text) => {
                window._lastCopiedText = text;
                return true;
            };
            document.execCommand = function(command, showUI, value) {
                if (typeof showUI === 'string') window._lastCopiedText = showUI;
                return true;
            };
        }""")

        # 稳妥监控绿色复制卡片加载
        try:
            page.wait_for_selector("//*[contains(text(), '复制')]", timeout=15000)
            print("账号卡片加载就位！")
        except:
            print("警告：卡片渲染超时，强制执行就地抓取...")

        # 定位所有成对出现的 复制账号 和 复制密码 按钮
        btn_accounts = page.locator("//*[contains(text(), '复制账号') or contains(text(), '复制帐号')]").all()
        btn_passwords = page.locator("//*[contains(text(), '复制密码')]").all()
        
        total_cards = min(len(btn_accounts), len(btn_passwords))
        print(f"数据通道就位！共检测到 {total_cards} 组账号，启动内存解密提取...")
        
        # --- 3. 驱动按钮点击，直接从网页变量里抓取解密后数据 ---
        for i in range(total_cards):
            try:
                # A. 触发第一个绿色按钮：复制账号
                page.evaluate("window._lastCopiedText = '';")
                btn_accounts[i].click()
                time.sleep(1.5) # 留出 1.5 秒等待后台异步接口解密
                
                raw_account_text = page.evaluate("window._lastCopiedText")
                print(f"-> [内存拦截成功] 第 {i+1} 组原始账号文本: {raw_account_text}")
                
                clean_username = clean_chinese_email(raw_account_text)
                
                # B. 触发第二个绿色按钮：复制密码
                page.evaluate("window._lastCopiedText = '';")
                btn_passwords[i].click()
                time.sleep(1.5)
                
                clean_password = page.evaluate("window._lastCopiedText")
                if clean_password:
                    clean_password = clean_password.strip()
                print(f"-> [内存拦截成功] 第 {i+1} 组纯净密码文本: {clean_password}")
                
                # C. 一对一严格按顺序有序组装
                if clean_username and clean_password and "无法获取" not in clean_username and "无法获取" not in clean_password:
                    res = (f"📍 地区：{escape_markdown('共享账号')}\n"
                           f"👤 账号：\n`{escape_markdown(clean_username)}`\n"
                           f"🔑 密码：`{escape_markdown(clean_password)}`")
                    if res not in account_data:
                        account_data.append(res)
                        print(f"🥇 【物理提纯成功】组 {i+1} => 账号: {clean_username} | 密码: {clean_password}")
            except Exception as inner_e:
                print(f"内存抓取第 {i+1} 组卡片发生跳过: {str(inner_e)}")
                continue

        browser.close()
    return account_data

def send_to_telegram_fixed(content_list):
    """发送数据，若内容为空则执行高情商通知闭环"""
    token = os.environ.get('BOT_TOKEN')
    chat_id = "-1003965538399"
    if not token: return

    # 💡 核心对齐升级：如果未获取到有效数据，通知频道不要发截图，保持整洁
    if not content_list:
        print("⚠️ [通道 4] 最终未捕获到任何有效数据，发送空号平安通知...")
        header = "🚀 *最新 Apple ID 共享更新提示*"
        status_str = "📍 状态：🔴 *当前暂无可用的活号*"
        body = f"📋 *通知提醒：*\n经系统实时动态监测，当前 *【通道 4】* 目标网站线上的所有共享 ID 已经全部处于锁定维护或异常状态，本次轮询未获取到有效活号。"
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

    print(f"成功获得 {len(content_list)} 个有效账号，正在组织高级排版向 TG 推送...")
    img_url = "https://raw.githubusercontent.com/qq83143750-a11y/telegram-web-monitor/main/1.jpg"
    
    header = f"🚀 *{escape_markdown('最新 Apple ID 共享更新【4】')}*"
    body = "\n\n" + "\n\n──────────────\n\n".join(content_list)
    
    tz_bj = timezone(timedelta(hours=8))
    bj_time = datetime.now(tz_bj).strftime('%Y-%m-%d %H:%M:%S')
    time_str = f"🕒 更新时间：{escape_markdown(bj_time)}"
    
    warning_str = f"⚠️ *{escape_markdown('警告：严禁在设置/iCloud中登录！')}*"
    notice_val = "共享🆔不能保持永久性，请第一时间下载，如若发生ID不可用情况，请持续关注频道等待两个小时更新，请谅解"
    notice_str = f"*{escape_markdown(notice_val)}*"
    
    follow_str = f"❤️ *{escape_markdown('欢迎关注我们交流群：')}*@bh888"
    service_str = f"            *{escape_markdown('客    服：')}*@zzyyy"
    
    caption = f"{header}\n{body}\n\n{time_str}\n{warning_str}\n\n{notice_str}\n\n{follow_str}\n{service_str}"
    
    # 严格限高保护，防止多账号字符爆表
    if len(caption) > 1024 and len(content_list) > 2:
        body = "\n\n" + "\n\n──────────────\n\n".join(content_list[:2])
        caption = f"{header}\n{body}\n\n{time_str}\n{warning_str}\n\n{notice_str}\n\n{follow_str}\n{service_str}"

    media_group = [{'type': 'photo', 'media': img_url, 'caption': caption, 'parse_mode': 'MarkdownV2'}]
    url = f"https://api.telegram.org/bot{token}/sendMediaGroup"
    
    res = requests.post(url, data={"chat_id": chat_id, "media": json.dumps(media_group)})
    if res.status_code == 200:
        print("🎉 物理拦截成功，Telegram 频道大图排版推送成功！")
    else:
        print(f"推送失败，TG服务器返回: {res.text}")

if __name__ == "__main__":
    data = get_apple_ids()
    send_to_telegram_fixed(data)
