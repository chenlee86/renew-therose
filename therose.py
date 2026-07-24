#!/usr/bin/env python3

import os, re, sys, time, requests
from seleniumbase import SB

# 环境变量 
EMAIL = os.environ.get("EMAIL") or ""            # 邮箱   
PASSWORD = os.environ.get("PASSWORD") or ""      # 密码
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or ""  # tg通知 bot token
TG_CHAT_ID = os.environ.get("TG_CHAT_ID") or ""      # tg通知 chat_id id

BASE_URL = "https://client.therose.cloud/login"

# --- 新增: 需要重启的目标服务器 URL ---
SERVER_URL = os.environ.get("SERVER_URL") or "https://panel.therose.cloud/server/1ce3ddfb"

# logo 图片路径（和脚本放在同一目录下，文件名 logo.png，仓库里需要提交这个文件）
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")

# --- 代理配置（由工作流 shell 脚本写入 $GITHUB_ENV）---
IS_PROXY = os.environ.get('IS_PROXY', 'false').lower() == 'true'
PROXY_SERVER = os.environ.get('PROXY_SERVER') or "socks5://127.0.0.1:1080"
REQUESTS_PROXIES = {"http": PROXY_SERVER, "https": PROXY_SERVER} if IS_PROXY else None

# 检查必要变量
if not EMAIL or not PASSWORD:
    print("❌ 请设置环境变量 EMAIL 和 PASSWORD")
    sys.exit(1)

# 获取当前出口IP
def get_current_ip(proxy_server=None):
    proxies = {"http": proxy_server, "https": proxy_server} if (proxy_server and IS_PROXY) else None
    try:
        resp = requests.get("https://api.ip.sb/ip", proxies=proxies, timeout=15)
        if resp.status_code == 200:
            return resp.text.strip()
        return "获取失败"
    except Exception as e:
        print(f"❌ 获取出口IP失败: {e}")
        return "获取失败"

# 点击续期按钮
def click_extend_button(sb):
    selectors = [
        'span:contains("Extend")',
        'button:contains(title="Extend")',
    ]
    for sel in selectors:
        try:
            if sb.find_element(sel, timeout=2):
                print(f"✅ 找到按钮，选择器: {sel}")
                sb.uc_click(sel, timeout=5)
                print("✅ 点击成功")
                return True, {}
        except:
            continue
    try:
        btn = sb.find_element('button:contains("Extend")', timeout=2)
        sb.driver.execute_script("arguments[0].click();", btn)
        print("✅ 通过 JavaScript 点击成功")
        return True, {}
    except Exception as e:
        err = str(e)
        # 服务商只有到期前半小时才会显示 Extend 按钮，找不到按钮多半是还没到时间，而不是真的出错
        not_time = "was not found" in err or "NoSuchElement" in err
        return False, {"error": err, "not_time": not_time}

# 检查续期是否成功
def check_renewal_success(sb):
    """检查是否出现续期成功的提示"""
    success_selectors = [
        '.alert-success',
        '.alert.alert-success',
        'div[role="alert"].alert-success',
        'div.alert-success',
        'span:contains("successfully purchased")',
        'div:contains("successfully purchased")'
    ]
    
    print("⏳ 等待5秒检查续期结果...")
    time.sleep(5)
    
    for selector in success_selectors:
        try:
            element = sb.find_element(selector, timeout=2)
            if element:
                text = element.text
                print(f"✅ 发现成功提示！选择器: {selector}")
                print(f"📝 提示内容: {text}")
                return True, text
        except:
            continue
    
    # 如果没有找到特定选择器，检查页面源码是否包含成功关键词
    try:
        page_source = sb.get_page_source()
        if "successfully purchased" in page_source.lower():
            print("✅ 页面源码中发现 'successfully purchased' 关键词")
            return True, "服务器已成功续期"
    except:
        pass
    
    return False, "未检测到续期成功提示"

# --- 新增函数: 执行服务器重启 ---
def restart_server(sb, url):
    """访问目标服务器页面并执行重启指令"""
    print(f"🔄 开始执行重启流程: 打开页面 {url}")
    try:
        sb.open(url)
        sb.wait_for_ready_state_complete()
        sb.sleep(3) # 等待页面元素加载（Pterodactyl等面板通常需要渲染时间）
        
        # 兼容常见的面板重启按钮
        restart_selectors = [
            'button:contains("Restart")', 
            'button[data-action="restart"]', 
            'button:contains("重启")'
        ]
        
        clicked = False
        for sel in restart_selectors:
            if sb.is_element_visible(sel):
                print(f"🎯 找到重启按钮: {sel}")
                sb.uc_click(sel)
                clicked = True
                break
                
        if clicked:
            print("✅ 成功点击重启按钮，等待命令执行生效...")
            sb.sleep(5)
            return True, "重启命令已成功下发"
        else:
            print("⚠️ 未找到任何重启按钮，可能面板已变更或账号无权限")
            # 出错时不抛出异常退出，只返回失败，确保流程顺畅
            return False, "页面上未检测到重启按钮"
            
    except Exception as e:
        err_msg = f"访问或重启服务器时发生异常: {e}"
        print(f"❌ {err_msg}")
        return False, err_msg

# 发送tg通知
def send_tg(token, chat_id, message):
    if not token or not chat_id:
        return
    message = f"【TheRose Cloud】\n{message}"

    if os.path.exists(LOGO_PATH):
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        try:
            with open(LOGO_PATH, "rb") as f:
                resp = requests.post(
                    url,
                    data={"chat_id": chat_id, "caption": message},
                    files={"photo": f},
                    timeout=15,
                    proxies=REQUESTS_PROXIES,
                )
            if resp.status_code == 200:
                print("📨 Telegram 通知已发送（带 logo）")
                return
            else:
                print(f"⚠️ 带 logo 发送失败，回退为纯文字: {resp.text}")
        except Exception as e:
            print(f"⚠️ 带 logo 发送异常，回退为纯文字: {e}")

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": message}, timeout=10, proxies=REQUESTS_PROXIES)
        if resp.status_code == 200:
            print("📨 Telegram 通知已发送")
        else:
            print(f"❌ Telegram 发送失败: {resp.text}")
    except Exception as e:
        print(f"❌ Telegram 发送异常: {e}")

# 登录流程
def login(sb, email, password):
    print("🌐 打开登录页面...")
    print("⏳ 等待页面加载...")
    sb.open(BASE_URL)
    sb.wait_for_ready_state_complete()
    sb.sleep(1)
    print("📧 填写邮箱...")
    sb.type('#login_form_email', email, timeout=10)
    print("🔑 填写密码...")
    sb.type('#login_form_password', password, timeout=10)
    time.sleep(1) 
    print("🛡 处理 Turnstile...")
    try:
        sb.uc_gui_click_captcha()
        print("✅ Turnstile 验证已处理")
    except Exception as e:
        print(f"⚠️ uc_gui_click_captcha 执行异常: {e}")
        
    print("⏳ 等待验证 token 生效...")
    sb.sleep(2)

    for attempt in range(3):
        print(f"🔑 点击登录按钮...(第 {attempt + 1} 次)")
        try:
            sb.uc_click('button:contains("Sign in")')
        except Exception as e:
            print(f"⚠️ 点击异常: {e}")

        for _ in range(5):
            current_url = sb.get_current_url()
            if "panel" in current_url:
                print("✅ 登录成功，已跳转到 Dashboard")
                return True, current_url
            time.sleep(1)

        try:
            err_selectors = ['.alert-danger', 'div[role="alert"].alert-danger', '.text-danger']
            for sel in err_selectors:
                if sb.is_element_visible(sel):
                    err_text = sb.get_text(sel)
                    print(f"❌ 登录出现错误提示: {err_text}")
                    sb.save_screenshot("login_faild.png")
                    return False, sb.get_current_url()
        except Exception:
            pass

        print("⚠️ 未跳转，可能是点击未生效或 token 还未就绪，准备重试...")

    print(f"❌ 登录失败，当前 URL: {sb.get_current_url()}")
    sb.save_screenshot("login_faild.png")
    return False, sb.get_current_url()

# 主流程
def main():
    print("🚀 启动浏览器")

    if IS_PROXY:
        print(f"⚙️ 代理已启用: {PROXY_SERVER}")
    else:
        print("🌐 直连模式（未使用代理）")

    current_ip = get_current_ip(PROXY_SERVER)
    print(f"🎯 当前出口IP: {current_ip}")

    sb_kwargs = {"uc": True, "headless": False}
    if IS_PROXY:
        sb_kwargs["proxy"] = PROXY_SERVER

    # 用以记录最终的通知内容
    final_tg_messages = []

    with SB(**sb_kwargs) as sb:
        success, url = login(sb, EMAIL, PASSWORD)
        
        if not success:
            msg = f"❌ 登录失败"
            print(msg)
            send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
            return

        print("📄 开始续期流程...")
        ok, info = click_extend_button(sb)
        
        if not ok:
            if info.get("not_time"):
                msg = "⏳ 未到续期时间，Extend 按钮尚未出现（一般到期前半小时才会开放），本次跳过"
                print(msg)
                final_tg_messages.append(msg)
            else:
                msg = f"❌ 点击 Extend 按钮失败: {info.get('error')}"
                print(msg)
                final_tg_messages.append(msg)
        else:
            time.sleep(1)
            try:
                button = sb.find_element('button:contains("Order now")', timeout=5)
                if button:
                    print("🛒 点击 Order now 按钮...")
                    sb.uc_click('button:contains("Order now")')
                    print("✅ 已点击 Order now 按钮")
                    
                    print("🔍 检查续期结果...")
                    renewal_success, renewal_msg = check_renewal_success(sb)
                    if renewal_success:
                        msg = f"✅ 续期成功！{renewal_msg}"
                        sb.save_screenshot("renewal_success.png")
                    else:
                        msg = f"❌ 续期可能失败: {renewal_msg}"
                        sb.save_screenshot("renewal_failed.png")
                    
                    print(msg)
                    final_tg_messages.append(msg)
                else:
                    msg = "❌ 未找到 Order now 按钮"
                    print(msg)
                    final_tg_messages.append(msg)
            except Exception as e:
                msg = f"❌ 点击 Order now 失败: {e}"
                print(msg)
                final_tg_messages.append(msg)

        # ==========================================
        # 续期执行完毕（无论成功还是跳过），执行重启流程
        # ==========================================
        restart_success, restart_msg = restart_server(sb, SERVER_URL)
        if restart_success:
            final_tg_messages.append(f"🔄 {restart_msg}")
        else:
            final_tg_messages.append(f"⚠️ 服务器重启失败: {restart_msg}")
            # 保存重启失败时的截图以便于调试排错
            sb.save_screenshot("restart_failed.png")
            
        # 汇总发送最终通知
        full_message = "\n".join(final_tg_messages)
        send_tg(TG_BOT_TOKEN, TG_CHAT_ID, full_message)

    print("🏁 脚本执行完毕")

if __name__ == "__main__":
    main()
