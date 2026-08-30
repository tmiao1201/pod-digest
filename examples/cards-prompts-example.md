# E250 mRNA 肿瘤疫苗 · 知识卡片 5 张（J 亚洲手账）

> **来源**：硅谷101 E250《mRNA的第二战场：对话英博，拆解Moderna人类首个肿瘤疫苗三期突破》digest 素材块①
> **风格**：J-asian-handnote（米黄笔记 + 中文手写 + 荧光高亮 + 贴纸 + 小机器人吉祥物）
> **规格**：5 张 · 3:4 竖版卡片 · 统一风格（Series lock 见下）
> **目标模型**：nanobanana (Gemini 2.5 Flash Image) / gpt-image-2（自然语言提示词，非 tag 流）
> **日期**：2026-08-29

---

## 全组通用风格前缀（每张提示词的开头 Style anchor）

```
A hand-written study-notes infographic (Asian "shou-zhang" / study journal style) on a
cream notebook-paper background with a faint grid. Heavy use of hand-written Chinese
text, key phrases highlighted with orange/yellow marker highlights and hand-drawn
circles. Blue hand-drawn rounded boxes divide the card into sections. Small stars and
emoji accents, plus a cute little AI-robot mascot sitting in the bottom-right corner
holding a tiny marker. Warm palette: cream + black handwriting + orange/yellow
highlighter + light-blue line boxes, occasional red/green dots. Friendly,
content-rich but organized, vertical 3:4 card.
```

## Series lock（5 张统一视觉）

- **锁定项**：J 风格锚点（上段全文）｜3:4 竖版｜暖米黄底 + 黑手写 + 橙/黄荧光 + 蓝色手绘圆角框｜小机器人吉祥物固定在右下角｜底部统一角标
- **可变项**：每张的主题、主体元素、分区结构、标题与文字清单
- **统一角标（每张底部小字）**：`手绘知识卡片 · 硅谷101 E250`

---

## 卡 1/5 · 一人一药

**Creative brief**：目标=讲清个体化 mRNA 肿瘤疫苗的端到端流程；读图顺序=标题→六步流水线→底部结论；受众=对医药科普感兴趣的一般读者；核心信息=每个病人的疫苗都是定制的。

**English prompt**
```
[Style anchor 见全组通用前缀]

Goal: explain how a personalized mRNA cancer vaccine is made for one single patient,
as a cheerful study-note card.

Canvas: vertical 3:4 card.

Layout (top to bottom): a large hand-written title with the key word circled in
orange marker; the middle two-thirds is a horizontal pipeline of exactly 6 stages
connected by hand-drawn wavy arrows, each stage inside a light-blue rounded box with
a black line doodle icon: (1) two small tissue chunks on a scalpel, (2) a sequencing
machine, (3) a laptop screen with glowing highlighted markers, (4) an mRNA strand
helix, (5) a round lipid nanoparticle capsule, (6) a syringe pointing back to a
simple human silhouette; bottom line is a short takeaway inside a yellow
highlighter bar.

Main elements: 6 doodle icons, wavy arrows, highlighter circles, mascot bottom-right.

Visual treatment: marker-style hand-drawn icons, one orange highlighter emphasis on
the title keyword only, short handwritten labels under each icon.

Constraints: keep all labels short and neat; the pipeline reads strictly left to
right.

Negative constraints: do not include a wall of body text, no photorealistic organs,
no dense English UI panels.
```

**Text manifest（逐字）**
| # | 文字 | 位置 | 层级 | 用途 |
|---|---|---|---|---|
| 1 | 一人一药 | 顶部大标题，"药"字套橙色荧光圈 | H1 | 标题 |
| 2 | One Patient, One Vaccine | 标题下小字 | H2 | 副题 |
| 3 | 取样 | 节点1下 | 标签 | 流程 |
| 4 | 测序 | 节点2下 | 标签 | 流程 |
| 5 | AI选新抗原 | 节点3下 | 标签 | 流程 |
| 6 | mRNA | 节点4下 | 标签 | 流程 |
| 7 | LNP包裹 | 节点5下 | 标签 | 流程 |
| 8 | 回输 | 节点6下 | 标签 | 流程 |
| 9 | 为每个病人定制一支专属疫苗 | 底部荧光条 | 结论 | 总结 |
| 10 | 手绘知识卡片 · 硅谷101 E250 | 右下角小字 | 角标 | 来源 |

**Control block**
- Exact count: exactly 6 pipeline stages connected left to right
- Relationship: each stage box connects to the next by a hand-drawn arrow; the 6th syringe points back to the human silhouette
- Exclusions: do not include extra stages, numbers, or side panels

---

## 卡 2/5 · 为什么必须联 PD-1

**Creative brief**：目标=讲清疫苗+PD-1 联用的互补机理；读图顺序=标题→左右两个动作→中央冲锋→底部等式；核心信息=点火+松刹车缺一不可。

**English prompt**
```
[Style anchor 见全组通用前缀]

Goal: explain why the personalized vaccine must combine with a PD-1 inhibitor.

Canvas: vertical 3:4 card.

Layout (top to bottom): a hand-written title with "PD-1" circled in orange marker;
the middle shows two side-by-side hand-drawn vignettes — on the LEFT a hand pulling
a brake lever off a wheel, on the RIGHT a hand striking a match that lights a small
fuse; below them in the center, a cheerful troop of round T-cell doodles charging
toward one spiky tumor cell; bottom line inside a yellow highlighter bar.

Main elements: brake-lever vignette, match vignette, T-cell troop, one spiky tumor
cell, arrows from both vignettes pointing down to the center, mascot bottom-right.

Visual treatment: one highlighter emphasis on "PD-1" in the title; each vignette
gets one short handwritten label with a light-blue rounded box.

Constraints: left vignette = brake release, right vignette = ignition, keep the two
clearly separated.

Negative constraints: do not include a wall of body text, no medical textbook
illustrations, no extra characters.
```

**Text manifest（逐字）**
| # | 文字 | 位置 | 层级 | 用途 |
|---|---|---|---|---|
| 1 | 为什么必须联 PD-1 | 顶部大标题，"PD-1"套荧光圈 | H1 | 标题 |
| 2 | 疫苗点火 | 右侧小景标签 | 标签 | 机理 |
| 3 | PD-1 松刹车 | 左侧小景标签 | 标签 | 机理 |
| 4 | 训练识别 | T 细胞队伍上方小字 | 说明 | 机理 |
| 5 | 解除抑制 | 同左侧标签下小字 | 说明 | 机理 |
| 6 | 1 + 1 > 2 | 底部荧光条 | 结论 | 总结 |
| 7 | 手绘知识卡片 · 硅谷101 E250 | 右下角小字 | 角标 | 来源 |

**Control block**
- Relationship: the brake-release vignette is on the LEFT and the ignition vignette is on the RIGHT; both point down to the T-cell troop in the center
- Exact count: exactly one spiky tumor cell facing the T-cell troop
- Exclusions: do not include extra organs, arrows, or text boxes

---

## 卡 3/5 · 跟复发赛跑（4-6 周制造）

**Creative brief**：目标=把 4-6 周生产时间表压进一张卡；读图顺序=标题→七节点时间轴（带时长）→沙漏→底部结论；核心信息=每一步都在跟肿瘤复发抢时间。

**English prompt**
```
[Style anchor 见全组通用前缀]

Goal: show the 4–6 week manufacturing timeline of one personalized vaccine as a race
against relapse.

Canvas: vertical 3:4 card.

Layout (top to bottom): a hand-written title with "4-6周" highlighted in orange; the
middle is a single horizontal hand-drawn timeline with exactly 7 round nodes
connected in a row, each node has a tiny clock face doodle and a short label; four
of the nodes carry a small duration tag in red handwriting; a large hourglass
doodle sits at the right end of the timeline; bottom line inside a yellow
highlighter bar.

Main elements: 7 clock nodes, wavy timeline, red duration tags, hourglass, mascot
bottom-right.

Visual treatment: timeline slightly tilted like a hand-drawn diagram; only the title
keyword gets the orange highlighter; duration tags in small red handwriting.

Constraints: the timeline reads strictly left to right; keep every label to a few
characters.

Negative constraints: do not include a wall of body text, no Gantt chart grid, no
extra decorative charts.
```

**Text manifest（逐字）**
| # | 文字 | 位置 | 层级 | 用途 |
|---|---|---|---|---|
| 1 | 跟复发赛跑 | 顶部大标题 | H1 | 标题 |
| 2 | Race Against Relapse | 标题下小字 | H2 | 副题 |
| 3 | 取样 | 节点1 | 标签 | 流程 |
| 4 | 测序 | 节点2 | 标签 | 流程 |
| 5 | AI预测 | 节点3＋红色小字「数天」 | 标签+时长 | 流程 |
| 6 | DNA模板 | 节点4＋红色小字「≤2周」 | 标签+时长 | 流程 |
| 7 | IVT | 节点5＋红色小字「1天」 | 标签+时长 | 流程 |
| 8 | LNP包封 | 节点6 | 标签 | 流程 |
| 9 | QC | 节点7＋红色小字「1-2周」 | 标签+时长 | 流程 |
| 10 | 术后窗口只有 4-6 周 | 底部荧光条 | 结论 | 总结 |
| 11 | 手绘知识卡片 · 硅谷101 E250 | 右下角小字 | 角标 | 来源 |

**Control block**
- Exact count: exactly 7 timeline nodes in one row
- Relationship: nodes connected strictly left to right; the hourglass sits at the right end
- Exclusions: do not include extra nodes, branches, or numeric tables

---

## 卡 4/5 · 把网撒大（34 个新抗原）

**Creative brief**：目标=用撒网隐喻讲新抗原覆盖与肿瘤逃逸；读图顺序=标题→上小网漏一条→下大网全兜住→底部结论；核心信息=覆盖越多、逃逸概率越低。

**English prompt**
```
[Style anchor 见全组通用前缀]

Goal: explain why the vaccine targets up to 34 neoantigens, using a fishing-net
metaphor for tumor escape.

Canvas: vertical 3:4 card.

Layout (top to bottom): a hand-written title with "34" circled in orange marker;
the card shows two stacked vignettes in light-blue rounded boxes — the UPPER
vignette is a small hand-drawn fishing net letting ONE mutant cell (spiky blob with
a tiny escape trail) slip through, the LOWER vignette is a much larger net with a
dense grid catching a whole crowd of spiky mutant cells; bottom line inside a
yellow highlighter bar.

Main elements: two nets (small upper, large lower), spiky cell doodles, a small
dashed escape trail in the upper vignette, short handwritten captions beside each
vignette, mascot bottom-right.

Visual treatment: the large net drawn with denser hand-drawn cross-hatch lines; one
orange highlighter emphasis on "34" in the title only.

Constraints: exactly one cell escapes in the upper vignette; no cell escapes in the
lower vignette.

Negative constraints: do not include a wall of body text, no realistic fish or
water, no extra vignettes.
```

**Text manifest（逐字）**
| # | 文字 | 位置 | 层级 | 用途 |
|---|---|---|---|---|
| 1 | 把网撒大 | 顶部大标题 | H1 | 标题 |
| 2 | Spread the Net | 标题下小字 | H2 | 副题 |
| 3 | 小网：漏掉 1 个 | 上格旁手写注 | 说明 | 隐喻 |
| 4 | 大网：34 个新抗原 | 下格旁手写注，"34"高亮 | 说明 | 隐喻 |
| 5 | 甩掉 1 个容易，同时甩掉 5 个？概率骤降 | 底部荧光条 | 结论 | 总结 |
| 6 | 手绘知识卡片 · 硅谷101 E250 | 右下角小字 | 角标 | 来源 |

**Control block**
- Relationship: the upper vignette lets exactly one cell escape; the lower vignette catches all cells
- Exclusions: do not include numeric axes, percentages, or extra captions

---

## 卡 5/5 · 疫苗 = 软件问题？

**Creative brief**：目标=呈现「马斯克说法 vs 一线创始人纠偏」的对峙；读图顺序=标题→左代码雨→右工厂+公章→底部结论；核心信息=算法在软件化、放行环节钉在物理世界。

**English prompt**
```
[Style anchor 见全组通用前缀]

Goal: stage the contrast between "vaccine as a software problem" and the founder's
on-the-ground correction.

Canvas: vertical 3:4 card.

Layout (top to bottom): a hand-written title ending with a big orange highlighted
question mark; the middle body is split into two halves by a hand-drawn vertical
lightning bolt — the LEFT half is green falling code-rain doodles behind a small
speech-bubble label, the RIGHT half is a tiny hand-drawn factory line with gears, a
red round official stamp and a small flip-calendar; a cut-out style avatar sticker
of a friendly cartoon scientist in a lab coat sits beside the right half with a
short name tag; bottom line inside a yellow highlighter bar.

Main elements: code-rain half, factory + stamp + calendar half, lightning divider,
avatar sticker with name tag, mascot bottom-right.

Visual treatment: the left half slightly cooler (green accents), the right half
warm (red stamp), handwriting stays dominant; one highlighter emphasis on the
question mark of the title.

Constraints: the lightning bolt divides the card into exactly two halves; the stamp
and calendar belong to the right half only.

Negative constraints: do not include a wall of body text, no real brand logos, no
realistic portraits, no extra panels.
```

**Text manifest（逐字）**
| # | 文字 | 位置 | 层级 | 用途 |
|---|---|---|---|---|
| 1 | 疫苗 = 软件问题？ | 顶部大标题，"？"套荧光圈 | H1 | 标题 |
| 2 | 马斯克：Yes | 左半气泡标签 | 标签 | 观点 |
| 3 | 英博 · 艾博生物CEO | 头像贴纸旁名签 | 署名 | 背书 |
| 4 | 放行那 2 周，软件快不了 | 右半气泡标签 | 观点 | 纠偏 |
| 5 | 算法在软件化，放行钉在物理世界 | 底部荧光条 | 结论 | 总结 |
| 6 | 手绘知识卡片 · 硅谷101 E250 | 右下角小字 | 角标 | 来源 |

**Control block**
- Relationship: the lightning bolt splits the body into exactly two halves; code-rain on the left, factory + stamp + calendar on the right
- Preservation: keep the avatar sticker clearly a friendly cartoon, not a real person's likeness
- Exclusions: do not include real company logos, prices, or URLs

---

## QA 自查（公共规范清单）

- 风格锚点：J 亚洲手账（米黄+手写+荧光+贴纸+吉祥物）✓
- 画布：5 张统一 3:4 ✓｜读图顺序：标题→主体→标签→结论 ✓
- Text manifest 逐字、分区、与提示词一致 ✓（每区单职责：标题/标签/说明/结论/角标）
- 事实来源：所有数字（4-6周、34、时长拆解、2周放行）均来自 E250 digest 已核验的嘉宾口述 ✓；无发明来源/价格/URL ✓
- Control block：镜1 六阶段计数、镜3 七节点计数、镜2/4/5 关系约束均已写入；无空块 ✓
- Series lock：5 张锁定风格/比例/色板/吉祥物/角标，主题与文字可变 ✓
