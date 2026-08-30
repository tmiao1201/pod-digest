# 内置卡片风格预设（公域通用，不依赖任何本地风格库）

> 用途：素材块① → 成套生图提示词的**默认风格底座**。三选一即可产出可直接粘贴给
> nanobanana / gpt-image / 即梦 / 豆包等任意生图模型的提示词。
> 本地若装有 Ted-imgstyle 风格库，可用其 14 风格替代（见 downstream.md 探测逻辑）。

三个预设的通用纪律（先读）：
- 画布 3:4 竖版知识卡，一套 3-6 张统一视觉（同底色/同字体气质/同角标位）
- 每张图文字 ≤40 字，标题/标签/结论各司其职，**禁止文字墙**
- 提示词结构固定：Style anchor → Goal → Canvas → Layout → Main elements → Visual treatment → Constraints → Negative constraints，另附 Text manifest（图中文字逐字清单）

---

## G1 · 手账笔记风（warm handnote）——默认推荐，科普/解读最搭

**Style anchor（直接复制用）**
```
A hand-written study-notes infographic (Asian "shou-zhang" study journal style) on a
cream notebook-paper background with a faint grid. Hand-written Chinese text, key
phrases highlighted with orange/yellow marker highlights and hand-drawn circles.
Blue hand-drawn rounded boxes divide the card into sections. Small stars and emoji
accents, a cute little robot mascot in the bottom-right corner. Warm palette: cream
+ black handwriting + orange/yellow highlighter + light-blue line boxes. Vertical
3:4 card, friendly and content-rich but organized.
```
**适合**：机理讲解、Q&A、新闻解读、需要亲切感的硬话题平民化
**注意**：手写中文短句最稳，挤就拆图

## G2 · 扁平信息图风（flat vector infographic）——数据/对比/流程最稳

**Style anchor**
```
A clean flat-vector infographic card, minimal modern tech style. White background,
two accent colors (deep blue #16405F + orange #E8833A) plus neutral grays. Simple
line icons, rounded rectangles, thin connector arrows, generous whitespace. Chinese
sans-serif headings with clear hierarchy. Vertical 3:4 card, crisp and professional,
no textures, no gradients, no 3D effects.
```
**适合**：流程拆解、时间轴、N 个概念并列、A/B 对比
**注意**：图标保持同一粗细线条；数字用大号强调色

## G3 · 黑白编辑风（editorial B/W）——严肃深度/商业史最配

**Style anchor**
```
An editorial magazine-style infographic, black and white with a single restrained
accent (deep red or brand blue) used only for one keyword per card. Serif Chinese
headline typography, thin rule lines dividing sections, small numbered markers,
subtle paper texture. High-contrast, serious, journalistic. Vertical 3:4 card with
strong typographic hierarchy.
```
**适合**：商业史叙事、行业格局判断、观点对峙类内容
**注意**：每张只允许一个强调色词；排版留白要大方

---

## 出提示词的最小流程（无 Ted-imgstyle 时）

1. 从 digest 素材块① 拿现成分镜表（镜号/画面内容/文字要点）
2. 选一个预设（拿不准就 G1）
3. 每张卡组装：Style anchor（上面抄）+ Goal/Canvas/Layout（按分镜填）+ Text manifest（文字要点逐字列）
4. 成套输出到一个 md 文件，逐镜小节，用户逐张粘贴给任意生图模型即可
