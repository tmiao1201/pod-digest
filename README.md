# pod-digest — 科技播客炼金炉

> Turn any podcast into an intelligence asset: transcript → evidence-graded digest → ready-to-use material blocks.
> 中文科技/商业播客与英文播客都支持，digest 恒为中文产出（金句双语）。

把「听播客」变成可积累的情报资产。一手产业信息往往先出现在播客访谈里（企业高管/创始人亲自发声），而不是研报里——本 skill 把它系统化：

```
任意播客（中/英/日…）
  → ① 字幕优先（有 YouTube 版：抓原语言字幕，秒级零成本）
  → ② 转写兜底（纯音频：Groq Whisper，免费 key 即可）
  → ③ digest（证据分级情报：🟢有数据/🟡单一口述/🔴利益相关 + 双语金句 + 术语表）
  → ④ 三个自包含素材块：知识卡片分镜 / 产业链四元组 / 金句精选
  → ⑤ 三个下游一句话触发：「出报告」（内置，digest→HTML 简报零依赖）/「出卡片」（内置三风格预设，或接 Ted-imgstyle）/「接产业链」（四元组交付，或接 chain-rotation）
```

## 安装（3 分钟）

```bash
# 依赖：python3 / curl / ffmpeg / yt-dlp（均可 brew install）
git clone <本仓库> ~/pod-digest && ln -s ~/pod-digest ~/.claude/skills/pod-digest

# 可选（纯音频转写才需要）：免费注册 https://console.groq.com/keys
export GROQ_API_KEY=gsk_xxx        # 或用 agent-reach: agent-reach configure groq-key <key>
# 有 YouTube 版的节目永远不需要 key
```

## 快速开始

```bash
python3 scripts/get_transcript.py "硅谷101" --match Moderna     # → out/episodes/.../transcript.txt
python3 scripts/scan_watchlist.py                               # 扫描订阅清单看更新
```

然后在 Claude Code 会话里说：「**digest 这期播客**」→ 产出 digest.md + 三素材块，机检通过后说「**出卡片**」或「**接产业链分析**」触发下游。

## 它和其他「播客总结」工具的区别

| 维度 | pod-digest |
|---|---|
| **证据分级** | 每条产业信息带 🟢有数据支撑/🟡单一口述/🔴利益相关 三级标签 + 具体利害标注（嘉宾谈自家产品=立场存疑） |
| **金句纪律** | 100% 机检逐字符回对逐字稿 + 说话人归属人工核对；回对不上降级为转述，绝不编造 |
| **机检门禁** | `verify_digest.py` 22 项检查：转写覆盖勾稽、四元组数值走私扫描、证据标签覆盖率……信封由脚本回写，手写会被覆写 |
| **下游开放** | 素材块自包含：卡片提示词喂任意生图模型；四元组附 tushare/akshare 三行代码数据自助指引 |

## 环境矩阵

| 能力 | 依赖 | 说明 |
|---|---|---|
| RSS 选集+音频下载 | python3 + curl | 零 key |
| YouTube 字幕 | yt-dlp（新版）+ 浏览器 cookie | 零 key，秒级 |
| 音频转写 | ffmpeg + GROQ_API_KEY（免费） | 或复用 agent-reach 托管 key |
| digest 生成 | Claude Code 会话 | 本 skill 的主体就是给会话 LLM 的作业指导 |
| 卡片/产业链下游 | 可选 | 内置 G1手账/G2扁平/G3黑白 三风格预设 + 数据自助指引，无下游也能用 |

## 示例（examples/）

- `digest-example-E250.md` — 真实 digest 节选版：证据三级标签/利益相关标注/三素材块完整结构（来源：硅谷101 E250，Moderna 肿瘤疫苗三期）
- `dashboard-mRNA-chain.png` — 下游产物：产业链兑现轮动仪表盘截图（四元组→chain-rotation，真实财务数据）
- `cards-prompts-example.md` — 下游产物：知识卡片成套生图提示词（素材块①→提示词，喂任意生图模型）

## 目录

`SKILL.md` 主流程 ｜ `references/` 获取路由/digest模板/下游衔接/卡片风格/本地私设 ｜ `scripts/` 获取转写+机检 ｜ `config/shows.yaml` 订阅清单示例（私单写 `shows.local.yaml`，不入库）

## 说明

- 逐字稿为第三方版权内容，`out/` 不入 git；本仓库只含代码与文档
- 转写引擎 Groq 是独立推理芯片公司（LPU），与马斯克 xAI 的 Grok 无关
- 仅供研究学习，非投资建议

MIT License.
