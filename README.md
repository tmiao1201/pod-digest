# pod-digest — 科技播客炼金炉

把「听播客」变成可积累的情报资产：**任意播客 → 带时间戳逐字稿 → 结构化 digest → 三个下游素材块**。

```
播客名/单集URL/订阅清单
  → ① 字幕优先（有YouTube版：yt-dlp 抓字幕，秒级零成本）
  → ② 转写兜底（Groq Whisper API：agent-reach 托管 或 GROQ_API_KEY 直连）
  → ③ digest（中文产出：产业情报/科技原理/术语表/双语金句，证据强度三级标注）
  → ④ 素材块（知识卡片分镜 / 产业链四元组 / 金句精选）
  → ⑤ 半自动下游（Ted-imgstyle 出卡片 / chain-rotation 产业链分析）
```

## 快速开始

```bash
# 环境体检（字幕路径零 key 可用；转写需 GROQ_API_KEY 或 agent-reach）
python3 scripts/get_transcript.py "硅谷101" --match Moderna   # → out/episodes/.../transcript.txt
# 之后在 Claude 会话里：digest 这期播客 → 生成 digest.md + 三素材块

# 订阅清单扫描（--scan：列出每个节目最新一集 + digest 状态）
python3 scripts/scan_watchlist.py
```

## 依赖与选项

| 能力 | 必需依赖 | 可选项 |
|---|---|---|
| RSS 选集+音频下载 | curl / python3（stdlib） | 无 |
| YouTube 字幕 | yt-dlp（新版）+ 浏览器 cookie | 无 key |
| 音频转写 | ffmpeg + GROQ_API_KEY（[免费注册](https://console.groq.com/keys)） | 或 agent-reach 托管 key |
| digest 生成 | Claude 会话（或任意长上下文 LLM） | — |
| 产业链数据填充 | — | tushare / akshare / 自备 / 纯定性（默认） |

## 设计原则

1. **字幕优先、转写兜底**——有视频版的节目永远不需要 key
2. **Hard Stop**——一步失败 3 次即停报人工，不瞎试
3. **digest 是情报不是复述**——每条产业信息带证据强度（🟢有数据/🟡单一口述/🔴利益相关）+ 利益相关标注 + 时间戳
4. **公域友好**——主流程零本地私货，引擎/数据源全部选项化，私设隔离在 `references/local-setup.md`
5. **多语言兼容**——转写保留原文（whisper 自动检测），digest 恒中文，金句双语，外文必出术语表

## 文档地图

- `SKILL.md` — 主流程（Claude 会话按此执行）
- `references/acquisition.md` — 获取路由 + 实测坑
- `references/digest-format.md` — digest 模板 + 证据标签 + 素材块 schema
- `references/downstream.md` — 下游衔接 + 数据源选项
- `config/shows.yaml` — 订阅清单

## v1 边界

不做：定时自动推送、B站源（反爬）、说话人分离、微信读书/文章源、公域发布（只保证可发布性）。
