# 逐字稿获取路由（acquisition）

> 核心原则：**字幕优先（零成本秒级）、RSS 音频转写兜底（通用）、Hard Stop 不瞎试**。
> 国内外几乎所有播客都通过 RSS 分发——iTunes Search API → feedUrl → RSS 是唯一通用可靠路径。

## 路径总览

| 输入形态 | 路径 | 成本 |
|---|---|---|
| YouTube 链接/频道（节目有视频版） | `yt-dlp` 抓字幕（人工字幕优先，自动字幕兜底） | 免费秒级 |
| 播客名 / 小宇宙·Apple·Spotify 单集页链接 | 解析出播客名 → `itunes_search.sh` → RSS → `parse_feed.py` 选集 → 音频下载 → 转写 | 免费额度内 |
| RSS 直链 | 跳过 iTunes，直接 `parse_feed.py` | 同上 |
| 本地音频文件 | 直接 `transcribe.sh` | 同上 |

## 主路径详解（播客名 → transcript）

```bash
# 1. 找 feed（iTunes API 直连无需代理；CN 无果自动试 US）
scripts/itunes_search.sh "硅谷101"

# 2. 看集数（可选）
scripts/parse_feed.py "https://feeds.fireside.fm/sv101/rss" --list 15

# 3. 一条龙：选集+下载+转写+落盘 out/episodes/<show>/<date>-<slug>/
scripts/get_transcript.py "硅谷101" --match Moderna --lang zh
scripts/get_transcript.py "硅谷101" --latest
```

选集逻辑：`--match` 多关键词时「全部命中」优先于「任一命中」，从新到旧取第一个；`E250` 这种集号是最稳的匹配词。

## 转写引擎（transcribe.sh --engine）

| 引擎 | 依赖 | 说明 |
|---|---|---|
| `agent-reach`（本地推荐） | `agent-reach` CLI + 其 groq key | key 委托 `agent-reach configure groq-key` 管理；失败自动降级 groq-direct |
| `groq-direct`（公域默认） | 仅 `GROQ_API_KEY` 环境变量 | 纯 stdlib 直连 Groq Whisper API（whisper-large-v3）；ffmpeg 按 15 分钟切段（每段约 5MB，免费档单文件 25MB 上限内），逐段转写后按偏移量拼时间戳 |
| `auto`（默认） | 自动探测 | 有可用 agent-reach 后端用它，否则有 GROQ_API_KEY 走直连，都没有则明确报错+指引 |

- 语言：`--lang auto`（默认，whisper 自动检测）｜`zh`/`en`/`ja`…（英文播客建议显式 `en`，准确度更好）
- 免费 Groq key：https://console.groq.com/keys（个人日常用量免费档够用）
- Groq 是独立推理芯片公司（LPU，前 Google TPU 架构师创办），与马斯克 xAI 的 Grok 模型**无关**，只是都取名自科幻词 grok

## YouTube 字幕路径

```bash
scripts/get_transcript.py "硅谷101" --match E250 --youtube "https://www.youtube.com/watch?v=xxx"
```

环境要求（2026-08 实测）：
1. **yt-dlp 保持最新**：YouTube 反爬频繁更新，旧版会被 "Sign in to confirm you're not a bot" 或 JS challenge 拦截（本机用 brew：`brew upgrade yt-dlp`）
2. **需要浏览器 cookie**：`--cookies-from-browser chrome`（已内置于调用参数）；无登录态的干净环境大概率被拦
3. 自动字幕通常无标点/无说话人区分——digest 引擎能处理，但金句回对原话时注意

## 已验证的坑（Hard Stop 纪律）

| # | 坑 | 对策 |
|---|---|---|
| 1 | 小宇宙是 Next.js SPA，页面动态渲染 | web fetch / yt-dlp 直抓小宇宙全废，**走 iTunes→RSS** |
| 2 | 不要从小宇宙 URL 构造 podcast id 去猜页面 | 播客名 → iTunes Search API 是唯一可信入口 |
| 3 | RSS 音频 URL 有 302 重定向 | curl/python 跟随重定向（`-L`） |
| 4 | Spotify 独家节目无 RSS | 无解，明确告知用户跳过 |
| 5 | 同一步骤失败 3 次 | **立即停**，列出已试方案标记「需人工介入」，不要换姿势瞎重试 |
| 6 | YouTube 无 cookie 被反爬拦截 | 升级 yt-dlp + cookies-from-browser；仍失败→放弃字幕路径走转写 |
| 7 | RSS 里 itunes:duration 格式不一（秒/HH:MM:SS） | parse_feed.py 已统一换算成秒 |
| 8 | 英文播客转写不写死 zh | 默认 auto 检测；shows.yaml 按节目配 lang |
| 9 | 部分网络下 curl/urllib 直连 api.groq.com 被 TLS 指纹拦截（HTTP 403，换 UA/去 Expect 头均无效），python requests 栈却放行 | 实测于 2026-08 本机：groq-direct（curl 实现）在该网络不可用，本地默认走 agent-reach（requests 栈）；海外/普通网络 curl 路径正常——公域保留 groq-direct 作零依赖路径 |
| 10 | agent-reach 转写输出为 response_format=text：无时间戳、无标点 | digest 时间戳改用 shownotes 官方章节目录锚定；金句做标点重建并逐条子串回对；ASR 专名误转建对照表（见 E250 digest 附录样板） |
| 11 | whisper 处理中文音频的**幻觉片头/片尾**：无故冒出「请不吝点赞 订阅 转发 打赏支持明镜与点点栏目」等常见 YouTube 口播语（训练数据污染），忽左忽右实测首行即中招 | 检查 transcript 首尾行，此类幻觉行直接忽略，不要当作正文引用进 digest |

## 语言策略

- 转写层产出**原文**逐字稿（whisper 90+ 语种，英文最强）
- 翻译发生在 digest 层（会话 LLM 统一中文产出）：金句双语对照、外文必出术语表、专有名词保留英文
- 详见 `digest-format.md`
