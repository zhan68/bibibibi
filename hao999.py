import os
import requests
import time
import re
from datetime import datetime, timedelta, timezone

def escape_markdown(text):
    """转义 Telegram MarkdownV2 特殊字符"""
    escape_chars = r'_*[]()~`>#+-=|{}.!'
    return re.sub(f'([{re.escape(escape_chars)}])', r'\\\1', text)

def get_apple_ids_by_api():
    # 1. 从原网址 https://doc.bat520.cc/doc/8/ 中提取的核心分享特征 ID 是 "8"
    share_id = "8"
    
    # 2. 拼接出老毛面板标准的后端异步解密 API 接口地址
    api_url = f"https://doc.bat520.cc/api/share/{share_id}"
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Referer": "https://doc.bat520.cc/doc/8/",
        "X-Requested-With": "XMLHttpRequest"
    }
    
    print(f"正在直接请求后端解密 API 接口: {api_url}")
    
    try:
        # 直接发送网络请求，限时 15 秒防止挂起卡死
        response = requests.get(api_url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"❌ 接口请求失败，状态码: {response.status_code}")
            return None
            
        res_json = response.json()
        
        # 验证接口返回状态 (老毛面板一般 code=200 或 status=1 代表成功)
        if "data" not in res_json:
            print("❌ 接口未返回有效账户数据，可能是 share_id 改变或接口需密码")
            return None
            
        accounts_list = res_json["data"]
        # 如果 data 嵌套在更深层，如 res_json["data"]["accounts"]
        if isinstance(accounts_list, dict) and "accounts" in accounts_list:
            accounts_list = accounts_list["accounts"]
        elif isinstance(accounts_list, dict) and "list" in accounts_list:
            accounts_list = accounts_list["list"]
            
        if not isinstance(accounts_list, list):
            # 兼容：如果 data 直接是一个大字典，包裹了具体的列表
            if isinstance(res_json["data"], dict):
                accounts_list = res_json["data"].get("data", [])
        
        print(f"API 成功返回，共获取到 {len(accounts_list)} 组底层账号数据。开始执行状态正常过滤...")
        
        account_data = []
        
        for item in accounts_list:
            # 读取账号和密码
            username = item.get("username") or item.get("account") or item.get("name")
            password = item.get("password") or item.get("pwd")
            
            # 核心过滤判定：获取账号的运行状态
            # 在老毛分享框架的数据库中：
            # status 等于 1 或等于 "正常" / "状态正常" 代表完全可用的绿色卡片账户
            status = item.get("status")
            status_txt = str(item.get("status_txt", "") or item.get("remark", ""))
            
            is_valid = False
            # 判断状态是否正常 (支持数字 1 判定或文本判定)
            if status == 1 or status == "1" or "正常" in status_txt or status == "正常":
                if "异常" not in status_txt and "锁定" not in status_txt:
                    is_valid = True
                    
            if is_valid and username and password:
                username = username.strip()
                password = password.strip()
                
                res = (f"👤 账号：`{escape_markdown(username)}`\n"
                       f"🔑 密码：`{escape_markdown(password)}`")
                
                if res not in account_data:
                    account_data.append(res)
                    print(f"🎉【过滤通过】账号: {username} 状态确认为: [正常]")
            else:
                print(f"⚠️ [已跳过] 账号: {username} 状态不符 (status={status}, msg={status_txt})")
                
        return account_data

    except Exception as e:
        print(f"❌ API 穿透解析崩溃: {e}")
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
    print(f"TG 发送完成，状态码: {res.status_code}")

if __name__ == "__main__":
    # 直接运行极速 API 数据拉取
    data = get_apple_ids_by_api()
    send_to_telegram(data)
