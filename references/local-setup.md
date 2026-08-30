# 本地私设模板（你的机器环境记这里；真实私设写在本文件同目录 local-setup.local.md——已 gitignore，不入库）

> 公域用户：把你的私人环境按下面骨架填到 local-setup.local.md，主流程永远不读私货。

## 转写引擎
- agent-reach CLI 是否安装：`command -v agent-reach`（key 用 `agent-reach configure groq-key <key>` 托管）
- 未装则 `export GROQ_API_KEY=...`（groq-direct 引擎）
- 你的网络若拦 curl 直连 api.groq.com（403/断连）：改用 agent-reach 引擎或配 `GROQ_API_BASE` 代理

## YouTube 字幕
- yt-dlp 版本与升级方式（brew / pipx / 官方二进制）
- 浏览器 cookie 来源（chrome/firefox/safari，`PODDIGEST_YT_COOKIES` 可覆盖）

## 产业链数据层（可选，接自己的数据源时填）
- 数据接口：tushare token / akshare / 自建缓存——示例代码见 downstream.md
- 若本地有 chain-rotation 类 skill：其数据层调用方式

## 笔记/推送目的地（可选）
- Obsidian vault 或其他笔记库路径（digest「存进笔记」时用）
