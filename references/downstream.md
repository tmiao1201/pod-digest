# 下游衔接（downstream）—— 可选放大器，不是必需品

> **核心原则：digest + 三素材块本身就是终点交付物。**
> 卡片提示词是喂任意生图模型（nanobanana / gpt-image / 即梦 / 豆包…）的自然语言；
> 四元组表是自解释的投研底稿。下游 skill 只是放大器——有则全功能，无则内置 fallback。

## Step 3 出口：下游自动探测

```bash
# 会话内执行一次，按结果走分支
ls ~/.claude/skills/Ted-imgstyle/SKILL.md 2>/dev/null && echo "imgstyle=有" || echo "imgstyle=无"
ls ~/.claude/skills/chain-rotation/SKILL.md 2>/dev/null && echo "chain=有" || echo "chain=无"
```

### ① → 知识卡片（素材块①）

- **本地有 Ted-imgstyle**：走其生图流程（分镜过目→选风格→产提示词，上游预拆分镜照 trip-cards 模式），产物落其 outputs/
- **没有（公域默认）**：用 `references/card-styles.md` 的三预设（G1 手账/G2 扁平信息图/G3 黑白编辑）直接组装成套提示词——分镜表素材块①已备好，输出一个 md，用户逐张粘贴给任意生图模型
- 两种路径产出物等价：**模型无关的自然语言提示词 + 逐字 Text manifest**

### ② → 产业链分析（素材块②）

- **本地有 chain-rotation**（含 tsdata 数据层）：四元组映射成其 COMPANIES 清单跑兑现轮动仪表盘；红线不变——数值字段留空由数据层填，绝不编数字，播客口述只做定性背景
- **没有（公域默认）**：四元组表本身就是交付物。想补数据，三行代码自助：

```python
# 方案A：tushare（需自己 token，pro_api_data.daily_basic 拿 PE/市值）
import tushare as ts; pro = ts.pro_api("你的token")
pro.daily_basic(ts_code="688137.SH", fields="close,pe,total_mv").tail(1)
# 方案B：akshare（免费无 token）
import akshare as ak
ak.stock_zh_a_spot_em()[ak.stock_zh_a_spot_em()["代码"].str.contains("688137")]
```
- **数据源选项**：`local-tsdata`（本地私设）/ `tushare` / `akshare`（公域默认推荐，免费）/ `manual` / `qualitative`（纯定性，零依赖默认）

### ③ → 金句精选（素材块③）

无下游依赖：可直接复制用于分享/卡片文字层。

### ④ → Obsidian / 笔记软件（可选）

用户说「存进笔记」时按其本地配置复制 digest.md，无固定路径。

## 消费门槛

下游消费的前提 = 信封由 `verify_digest.py --write-envelope` 回写且 status=green——跳过机检=断下游。
