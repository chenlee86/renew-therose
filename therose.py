#!/usr/bin/env python3

import os, re, sys, time, requests
from seleniumbase import SB

# 环境变量 
EMAIL = os.environ.get("EMAIL") or ""            # 邮箱   
PASSWORD = os.environ.get("PASSWORD") or ""      # 密码
TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN") or ""  # tg通知 bot token
TG_CHAT_ID = os.environ.get("TG_CHAT_ID") or ""      # tg通知 chat_id id

# 目标服务器面板地址
SERVER_URL = os.environ.get("SERVER_URL") or "https://panel.therose.cloud/server/1ce3ddfb"
BASE_URL = "https://client.therose.cloud/login"

# logo 图片路径
LOGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")

# --- 代理配置 ---
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
        # 服务商只有到期前半小时才会显示 Extend 按钮
        not_time = "was not found" in err or "NoSuchElement" in err
        return False, {"error": err, "not_time": not_time}

# 检查续期是否成功
def check_renewal_success(sb):
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
                return True, text
        except:
            continue
    
    try:
        page_source = sb.get_page_source()
        if "successfully purchased" in page_source.lower():
            print("✅ 页面源码中发现 'successfully purchased' 关键词")
            return True, "服务器已成功续期"
    except:
        pass
    
    return False, "未检测到续期成功提示"

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
                    sb.save_screenshot("login_failed.png")
                    return False, sb.get_current_url()
        except Exception:
            pass
        print("⚠️ 未跳转，可能是点击未生效或 token 还未就绪，准备重试...")

    print(f"❌ 登录失败，当前 URL: {sb.get_current_url()}")
    sb.save_screenshot("login_failed.png")
    return False, sb.get_current_url()

# 执行重启服务器操作
def reboot_server(sb, url):
    print(f"🔄 准备进入服务器面板进行重启: {url}")
    try:
        sb.open(url)
        sb.wait_for_ready_state_complete()
        time.sleep(5) # 给面板一点时间加载状态
        
        # --- 处理控制面板需要独立登录的情况 ---
        if sb.is_element_visible('input[type="password"]'):
            print("🔒 检测到控制面板需要独立登录，正在尝试自动输入账号密码...")
            try:
                # 输入账号
                if sb.is_element_visible('input[name="user"]'):
                    sb.type('input[name="user"]', EMAIL)
                elif sb.is_element_visible('input[type="text"]'):
                    sb.type('input[type="text"]', EMAIL)
                
                # 输入密码
                sb.type('input[type="password"]', PASSWORD)
                time.sleep(1)
                
                # 处理 Turnstile 验证码
                print("🛡️ 处理控制面板的 Turnstile 验证码...")
                try:
                    sb.uc_gui_click_captcha()
                    print("✅ 控制面板 Turnstile 验证已点击")
                except Exception as e:
                    print(f"⚠️ 控制面板 Turnstile 处理异常 (可能已被免验证放行): {e}")
                
                print("⏳ 等待验证 token 生效...")
                time.sleep(3) 
                
                # 尝试点击登录按钮
                try:
                    sb.click('button:contains("Login")')
                except:
                    sb.click('button[type="submit"]')
                    
                print("⏳ 已提交控制面板登录，等待页面跳转...")
                time.sleep(8) # 登录后跳转可能较慢
            except Exception as e:
                print(f"⚠️ 自动登录控制面板发生错误: {e}")
        
        # --- [核心修复] 检查是否被强制重定向到了主列表页 ---
        current_url = sb.get_current_url()
        print(f"📄 登录后当前所在页面: {current_url}")
        
        # 如果当前链接里没有 "/server/"，说明不在详情页，需要重新跳转
        if "/server/" not in current_url:
            print("🔀 检测到停留在主列表页，正在强制进入目标服务器控制台...")
            sb.open(url)
            sb.wait_for_ready_state_complete()
            time.sleep(6) # 给详情页加载 WebSocket 和按钮的时间
        # --- 新增结束 ---

        # 兼容更多 Pterodactyl/Reviactyl 面板的重启按钮标识
        reboot_selectors = [
            'button[data-action="restart"]',     # 翼龙面板原生按钮属性 (最精准)
            'button[aria-label="Restart"]',      # 英文无障碍标签
            'button[aria-label="重启"]',         # 中文无障碍标签
            'button:contains("Restart")',        # 英文文本
            'button:contains("Reboot")',         # 英文文本
            'button i.fa-sync'                   # 同步/刷新图标
            'button[data-action="restart"]',     # 原生 data-action 属性
            'div.flex.items-center button:nth-child(3)', # 右上角操作区的第3个按钮
            'div.flex.items-center button:nth-child(2)', # 右上角操作区的第2个按钮
            'button i.fa-redo',                  # 带有 redo 循环图标
            'button i.fa-sync',                  # 带有 sync 同步图标
            'button:has(i.fa-redo)',
            'button:has(i.fa-sync)'
        ]
        
        btn_clicked = False
        for sel in reboot_selectors:
            try:
                if sb.is_element_visible(sel):
                    print(f"✅ 找到重启按钮，选择器: {sel}")
                    sb.uc_click(sel)
                    btn_clicked = True
                    break
            except:
                continue

        # 降级方案：利用坐标或 JS 强制点击右上角重启按钮
        if not btn_clicked:
            try:
                # 尝试直接抓取带有 data-action 的按钮
                btn = sb.find_element('button[data-action="restart"]', timeout=3)
                sb.driver.execute_script("arguments[0].click();", btn)
                btn_clicked = True
                print("✅ 通过 JavaScript (data-action) 点击重启成功")
            except:
                # 终极降级：直接通过右上角按钮容器的常见特征用 JS 点击
                try:
                    sb.driver.execute_script("""
                        const buttons = document.querySelectorAll('div.flex.items-center button, .card button');
                        for (let btn of buttons) {
                            if (btn.innerHTML.includes('fa-redo') || btn.innerHTML.includes('fa-sync') || btn.getAttribute('data-action') === 'restart') {
                                btn.click();
                                return true;
                            }
                        }
                        // 如果找不到特定图标，尝试点右上角操作区的最后一个按钮
                        if (buttons.length > 0) {
                            buttons[buttons.length - 1].click(2);
                            return true;
                        }
                    """)
                    btn_clicked = True
                    print("✅ 通过通用 JS 脚本触发了重启按钮")
                except Exception as ex:
                    print(f"⚠️ JS 降级点击失败: {ex}")
                
        # 降级方案：JS 强制点击
        if not btn_clicked:
            try:
                btn = sb.find_element('button[data-action="restart"]', timeout=2)
                sb.driver.execute_script("arguments[0].click();", btn)
                btn_clicked = True
                print("✅ 通过 JavaScript (data-action) 点击重启成功")
            except:
                pass
                
        if btn_clicked:
            print("⏳ 等待重启命令发送...")
            time.sleep(3)
            return True, "已成功发送重启指令"
        else:
            return False, "页面上未检测到重启按钮 (可能面板未完全加载)"
            
    except Exception as e:
        return False, f"重启操作发生异常: {e}"
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

    with SB(**sb_kwargs) as sb:
        success, url = login(sb, EMAIL, PASSWORD)
        
        if not success:
            msg = f"❌ 登录失败，请检查账号密码或验证码拦截情况。"
            print(msg)
            send_tg(TG_BOT_TOKEN, TG_CHAT_ID, msg)
            return

        print("📄 开始续期流程...")
        ok, info = click_extend_button(sb)
        
        # 续期逻辑
        if not ok:
            if info.get("not_time"):
                msg_renewal = "⏳ 未到续期时间，Extend 按钮尚未出现（一般到期前半小时开放），本次跳过。"
            else:
                msg_renewal = f"❌ 续期失败，未找到 Extend 按钮 ({info.get('error')})。"
            print(msg_renewal)
        else:
            time.sleep(1)
            try:
                button = sb.find_element('button:contains("Order now")', timeout=5)
                if button:
                    print("🛒 点击 Order now 按钮...")
                    sb.uc_click('button:contains("Order now")')
                else:
                    msg_renewal = "❌ 续期异常，未找到 Order now 按钮。"
                    print(msg_renewal)
            except Exception as e:
                msg_renewal = f"❌ 点击 Order now 发生错误: {e}。"
                print(msg_renewal)
            
            print("🔍 检查续期结果...")
            renewal_success, renewal_msg = check_renewal_success(sb)
            if renewal_success:
                msg_renewal = f"✅ 续期成功！{renewal_msg}"
                sb.save_screenshot("renewal_success.png")
            else:
                msg_renewal = f"❌ 续期可能失败: {renewal_msg}"
                sb.save_screenshot("renewal_failed.png")
            print(msg_renewal)

        # 重启逻辑 (与续期独立，均会执行)
        print("🔄 开始检查并执行服务器重启...")
        reboot_ok, reboot_msg = reboot_server(sb, SERVER_URL)
        
        if reboot_ok:
            msg_reboot = f"✅ 自动重启成功: {reboot_msg}"
            sb.save_screenshot("reboot_success.png")
        else:
            msg_reboot = f"⚠️ 重启失败: {reboot_msg}"
            sb.save_screenshot("reboot_failed.png")
        print(msg_reboot)
        
        # 汇总发送通知
        final_msg = f"{msg_renewal}\n---\n{msg_reboot}"
        send_tg(TG_BOT_TOKEN, TG_CHAT_ID, final_msg)

    print("🏁 脚本执行完毕")

if __name__ == "__main__":
    main()
