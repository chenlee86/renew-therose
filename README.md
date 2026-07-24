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


