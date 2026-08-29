# 下游衔接（downstream）—— 素材块怎么喂给下游 skill

> 半自动原则：digest 产出结构化素材块，**用户点头才触发下游**。
> **消费门槛**：下游消费的前提 = 信封由 `verify_digest.py --write-envelope` 回写且 status=green——跳过机检=断下游，逃逸无收益。
> 原因：Ted-imgstyle 有两道强制人工确认门（分镜过目、风格选定）；chain-rotation 单次跑 15-30 分钟，
> 只有本期产业情报足够密（四元组 ≥ 5 行）才值得跑。

## ① → Ted-imgstyle（知识卡片）

接法照抄 `trip-cards` skill 的模式（上游预拆分镜 → 调用 Ted-imgstyle 出提示词）：

1. 从素材块①拿现成的分镜表（镜号/画面内容/文字要点三字段已备好）
2. 调用 Ted-imgstyle skill 走生图流程，告知：
   - 比例 3:4、张数 = 分镜数
   - 风格：用素材块①里的建议代号（用户可换）
   - 文字要点逐字使用（Ted-imgstyle 的 Text manifest 要求逐字）
3. 产物落 `~/cc/Ted-imgstyle/outputs/` 或桌面 `*_生图提示词.md`
4. 后续生图（nanobanana / gpt-image-2）由用户在 Ted-imgstyle 流程里完成

## ② → chain-rotation（产业链兑现轮动）

1. 从素材块②读出：产品锚点 + 四元组清单 + 证据强度
2. 调用 chain-rotation skill，把四元组映射成它的 `COMPANIES` 清单格式
   （`环节, 名称, 代码, 兑现节奏标签` 四列；代码列留空让它落）
3. **红线**：播客口述观点属于定性证据——chain-rotation 的数值字段
   （估值/涨跌/PE 分位等）一律由数据层算，digest 不提供也不暗示数字
4. 口述节奏标签在它的体系里只能给「弱/中证据强度」，提示语里注明来源是播客访谈

### 数据源选项（data_source）

四元组的代码/财务数据填充，按用户环境选：

| 选项 | 依赖 | 适用 |
|---|---|---|
| `local-tsdata` | 本地 tsdata 数据层（见 local-setup.md） | 本机默认 |
| `tushare` | 用户自己的 tushare token | 公域用户（有 token） |
| `akshare` | `pip install akshare`，免费无 token | 公域默认推荐 |
| `manual` | 用户自备数据文件 | 特殊情况 |
| `qualitative` | 不拉数，纯定性四元组 | 发布版默认/快速浏览 |

发布版默认 `qualitative`（零依赖跑通），本地默认 `local-tsdata`。

## ③ → 金句精选

无固定下游：直接复制可用于朋友圈/知识星球/卡片文字层。若用户要求，
也可作为素材块①中某张卡片的文字要点。

## ④ → 第二大脑 / Obsidian（可选）

用户说「存进大脑」时：把 digest.md 复制进 Obsidian vault 的捕获目录
（路径见 `references/local-setup.md`，属于本地私设）。
