---
name: pod-digest
description: |
  科技播客炼金炉：任意播客 → 带时间戳逐字稿 → 结构化 digest（产业情报/科技原理/金句/术语表）
  → 三个下游素材块（知识卡片分镜草案/产业链四元组草案/金句精选），半自动接 Ted-imgstyle 与 chain-rotation。
  触发词：「digest 这期播客」「炼一下硅谷101最新一期」「播客digest」「pod-digest」
  「提取播客逐字稿」「播客转写总结」「这期播客讲了什么值得听的」。
  适用：任意 RSS 分发的播客（小宇宙/Apple/Spotify/喜马拉雅上的非独家节目，中英文皆可）、有 YouTube 版的节目。
  不适用：Spotify 独家无 RSS 节目；微信读书/文章类内容（留给 v2）；只要下载音频不需要 digest。
---

# pod-digest — 科技播客炼金炉

> 一手产业信息往往先出现在播客访谈里（企业高管/创始人亲自发声），而不是研报里。
> 本 skill 把「听播客」变成可积累的情报资产：逐字稿 → digest → 素材块 → 下游框架。

## 核心纪律（先读这个）

1. **字幕优先，转写兜底**——节目有 YouTube 版先抓字幕（秒级零成本），纯音频才转写（详见 `references/acquisition.md`）
2. **Hard Stop**——任何一步失败 3 次立即停，列已试方案报「需人工介入」，不换姿势瞎试
3. **digest 是情报不是复述**——每条产业信息必须带证据强度标签和利益相关标注；嘉宾谈自家产品 = 立场存疑
4. **金句必须原话回对**——从 transcript 逐字摘，不润色不编造；转写存疑处标 `[?]`
5. **输出恒为中文**（转写层保留原文，翻译在 digest 层做，规则见 `references/digest-format.md`）

## 使用流程

### Step 0：环境体检（首次/报错时）

```bash
# 转写引擎可用性（字幕路径不需要任何 key）
ls ~/.local/bin/agent-reach 2>/dev/null && agent-reach doctor --json | head -30
echo "GROQ_API_KEY=${GROQ_API_KEY:+已设置}"
```

两个都没有 → 只能走字幕路径，遇到纯音频节目明确告知用户怎么配（见 `.env.example`），不要卡死。

### Step 1：获取逐字稿

```bash
cd ~/cc/pod-digest
# 常见三种入口
python3 scripts/get_transcript.py "硅谷101" --match Moderna          # 按关键词选集
python3 scripts/get_transcript.py "硅谷101" --latest                  # 最新一期
python3 scripts/get_transcript.py "硅谷101" --match E250 \
    --youtube "https://www.youtube.com/watch?v=xxx"                   # 有YouTube版，抓字幕免转写
```

产物：`out/episodes/<节目>/<日期>-<slug>/transcript.txt + meta.json`（meta 含 shownotes——章节目录和嘉宾信息是 digest 的重要输入）。

选集/搜索引擎/踩坑 → `references/acquisition.md`。

### Step 2：生成 digest

读 `transcript.txt` 全文 + `meta.json` 的 shownotes，按 `references/digest-format.md` 的模板写 `digest.md` 到同目录。

关键动作：
- 优先用 shownotes 的官方章节目录对齐时间戳（比 whisper 的更准）
- 产业情报逐条标证据强度（🟢有数据/🟡单一口述/🔴利益相关）
- 外文播客：digest 中文、金句双语、必出术语表
- 跳过广告/口播/社群推广段（情报型 agent 的去噪职责）

### Step 3：素材块 + 下游（半自动，两个等价选项）

digest 末尾固定产出三块（schema 见 `references/digest-format.md`）：
① 知识卡片分镜草案 ② 产业链四元组草案 ③ 金句精选。

下游由用户一句话触发，两个选项平级：
- 用户说「**出卡片**」→ 素材块① 喂 Ted-imgstyle 走生图流程（衔接见 `references/downstream.md`）
- 用户说「**接产业链**」或「**出产业链分析**」→ 素材块② 喂 chain-rotation：四元组映射成 COMPANIES 清单，数值字段留空由数据层填，**绝不编数字**；若素材块②已判定「本期不适合」（A股映射弱/证据链薄），如实告知并给出可自研的延伸方向，不硬凑

### Step 4：信封落盘

digest 完成后写 `out/envelopes/pod-digest.json`：

```json
{"id":"pod-digest","type":"intel","date":"<digest日期>","status":"green",
 "headline":"<本期一句话价值>","deliverable":{"md":"<digest.md相对路径>"},
 "self_check":"<金句回对/时间戳抽查结论>","generated_at":"<ISO时间>"}
```

## 文件地图

| 路径 | 说明 |
|---|---|
| `scripts/get_transcript.py` | 主入口：选集+下载+转写一条龙（幂等） |
| `scripts/itunes_search.sh` / `parse_feed.py` / `transcribe.sh` / `transcribe_groq.py` | 分步工具（acquisition.md 有详解） |
| `references/acquisition.md` | 获取路由 + 8 条实测坑 + Hard Stop 纪律 |
| `references/digest-format.md` | digest 模板逐节规范 + 证据强度标签 + 素材块 schema |
| `references/downstream.md` | Ted-imgstyle / chain-rotation 衔接 + 数据源选项 |
| `references/local-setup.md` | 本地私设（发布公域时整体替换为通用安装指引） |
| `config/shows.yaml` | 订阅清单（watchlist） |
| `out/episodes/<show>/<date>-<slug>/` | transcript.txt / digest.md / meta.json |
