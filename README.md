# A股每日复盘 · 云端版（GitHub Actions + DeepSeek）

每个交易日北京时间 **18:00** 自动运行在 GitHub 云端（**与你电脑开不开机无关**）：
抓取 A 股真实行情 → DeepSeek 生成分析 → 邮件发送到你的邮箱。

## 工作原理
- 指数（上证/深证成指/创业板指/科创50，含成交额）= 新浪财经 API
- 板块涨跌榜、涨停家数 = 东方财富 API
- 财经快讯（best-effort）= 东方财富 7x24
- 解读 / 消息面 / 次日策略 = DeepSeek（`deepseek-chat`）
- 发信 = Gmail SMTP

非交易日（节假日）会自动识别并跳过，不发邮件。

## 部署步骤（约 5 分钟）

### 1. 新建 GitHub 仓库
在 GitHub 上新建一个 **private（私有）** 仓库，例如 `a-stock-daily`（先不要勾选任何初始化文件）。

### 2. 推送代码
在本目录（`F:\A股\a-stock-cloud`）执行（把 URL 换成你的仓库地址）：
```powershell
git remote add origin https://github.com/<你的用户名>/a-stock-daily.git
git branch -M main
git push -u origin main
```

### 3. 配置 Secrets（密钥）
仓库页面 → **Settings → Secrets and variables → Actions → New repository secret**，逐个添加：

| Name | Value |
|---|---|
| `DEEPSEEK_API_KEY` | 你的 DeepSeek API key |
| `GMAIL_USER` | `longrain153@gmail.com` |
| `GMAIL_APP_PASSWORD` | 你的 Gmail 16 位应用专用密码 |
| `MAIL_TO` | `longrain153@gmail.com`（收件人，可填多个用逗号分隔） |

> 这些值只存在 GitHub 加密 Secrets 里，不会出现在代码或日志中。

### 4. 手动测试一次
仓库页面 → **Actions → 选「A股每日复盘」→ Run workflow**（手动触发）。
等 1-2 分钟，查看运行日志是否成功、邮箱是否收到。成功后即每个交易日 18:00 自动运行。

## 注意事项
- **定时延迟**：GitHub Actions 的 cron 在高峰期可能延迟几分钟到几十分钟触发，属正常现象。
- **数据可达性**：本工作流从 GitHub 海外服务器访问新浪/东方财富接口。绝大多数情况可正常访问；若首次手动运行日志显示数据抓取失败，可能是接口对海外 IP 限制，需要换数据源或换运行地域，届时再调整。
- **休眠保护**：若仓库连续 60 天无提交，GitHub 会暂停其定时任务（届时手动触发或推一次提交即可恢复）。
- 修改发送时间：编辑 `.github/workflows/daily.yml` 里的 cron（UTC 时间，北京时间 = UTC + 8）。

## 本地结构
```
main.py                      取数 + DeepSeek + 发信 主程序
requirements.txt             依赖
.github/workflows/daily.yml  定时任务定义
```
