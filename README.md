# 🌟 therose.cloud 自动续期与服务器重启脚本

本项目是一个基于 Python 和 SeleniumBase 编写的自动化脚本，专为 therose.cloud 提供无人值守的服务器自动续期（Extend）与自动状态维护（登录控制台并重启服务器）服务。

## ✨ 核心功能
* 🤖 **自动人机验证**：在无头（Headless）浏览器模式下，自动识别并处理 Cloudflare Turnstile 等盾牌验证码。
* 🔄 **智能续期**：自动检测并点击服务器续期按钮，避免服务器因超时未续期被系统回收。
* 🔌 **面板无缝重启**：自动穿透控制面板（Panel）的独立二次登录，精准识别并触发基于翼龙（Pterodactyl/Reviactyl）面板的服务器重启逻辑。
* 📢 **消息推送**：集成 Telegram 通知，无论执行成功还是遇到异常，运行结果均一目了然。

---

## 🔐 环境变量 (Environment Variables) 配置

无论是在本地调试运行，还是在 GitHub Actions 中部署，脚本都依赖以下环境变量来读取账户信息并保护你的隐私数据（切勿将明文密码硬编码写在 `.py` 文件中）。

| 变量名 (Name) | 必填 | 说明 |
| :--- | :--- | :--- |
| `EMAIL` | ✅ 是 | 你的 therose.cloud 账户注册/登录邮箱。 |
| `PASSWORD` | ✅ 是 | 你的账户登录密码。 |
| `TELEGRAM_BOT_TOKEN` | ❌ 否 | 你的 Telegram 机器人 Token（用于发送通知，形如 `123456:ABC-DEF...`）。如果不需要 TG 通知可不配置。 |
| `TELEGRAM_CHAT_ID` | ❌ 否 | 接收 TG 通知消息的目标账户 ID 或群组 ID。 |

---

## 🚀 部署指南 (GitHub Actions 推荐)

推荐使用 GitHub Actions 实现完全免费的云端定时自动化运行。

### 第一步：配置 GitHub Secrets
1. 进入你存放该脚本代码的 GitHub 仓库主页。
2. 依次点击顶部菜单栏的 **Settings** -> 左侧导航栏的 **Secrets and variables** -> **Actions**。
3. 点击绿色的 **New repository secret** 按钮。
4. 将上方表格中的【变量名】填入 `Name` 输入框，对应的值填入 `Secret` 输入框。
5. 重复添加，直到所有必填环境变量配置完成。

### 第二步：检查 Workflow 文件映射
确保你的仓库的 `.github/workflows/xxxx.yml` 文件中，环境变量已正确传递给了 Python 脚本：
```yaml
    env:
      EMAIL: ${{ secrets.EMAIL }}
      PASSWORD: ${{ secrets.PASSWORD }}
      TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }}
      TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }}
第三步：运行与查看日志
脚本会根据你在 workflow.yml 中设置的 cron 时间表达式自动定时触发。

你也可以在 GitHub 的 Actions 标签页中，选中对应的 Workflow 并点击 Run workflow 进行手动测试。

排错利器：如果运行失败，可以在该次运行记录的页面最下方下载 Artifacts (如 run-screenshots 压缩包)，通过查看截图确认失败原因（如面板断网、验证码未通过等）。

💻 本地调试运行指南
如果你需要在本地电脑或自己的 VPS 服务器上修改代码并调试：

1. 安装核心依赖
确保系统已安装 Python 3.8 或以上版本，然后安装核心依赖库：

Bash
pip install seleniumbase
2. 设置系统环境变量
在执行代码前，必须先在终端中声明变量：

Windows (CMD):

DOS
set EMAIL=你的邮箱
set PASSWORD=你的密码
Windows (PowerShell):

PowerShell
$env:EMAIL="你的邮箱"
$env:PASSWORD="你的密码"
Linux / macOS:

Bash
export EMAIL="你的邮箱"
export PASSWORD="你的密码"
3. 执行脚本
Bash
python therose.py
⚠️ 注意事项与已知问题
验证码拦截限制：如果目标站点近期遇到攻击或大幅提升了 Cloudflare 防护等级，SeleniumBase 偶尔可能会面临 Turnstile 无法自动点击通过的情况。建议遇到连续报错时，查看截图中盾牌的状态。

语言兼容性：重启逻辑使用了底层属性（如 data-action="restart" 或特定的 font-awesome 图标类名）来寻找按钮，理论上无论服务器面板设置为中文还是英文环境均可完美兼容。
