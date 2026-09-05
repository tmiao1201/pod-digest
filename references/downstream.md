# 下游衔接（downstream）—— 可选放大器，不是必需品

> 只请求摘要时，digest + 三素材块就是交付物；选择具体输出后继续完成相应成品。
> 卡片提示词是喂任意生图模型（nanobanana / gpt-image / 即梦 / 豆包…）的自然语言；
> 四元组表是自解释的投研底稿。下游 skill 只是放大器——有则全功能，无则内置 fallback。

## Step 3 出口：下游自动探测

按当前会话可用的 skill 和工具选择执行路径；不要假设用户一定安装在某个宿主的固定目录。

### ① → 知识卡片（素材块①）

- 用户要求实际图卡时，按 [codex-media.md](codex-media.md) 核验内容，调用当前生图工具，交付图片与逐字文案、提示词。Codex 中使用当前内置生图能力。
- 有 `ted-imgstyle` 时可以采用其风格；没有则用 [card-styles.md](card-styles.md) 的 G1 手账、G2 扁平信息图或 G3 黑白编辑。
- 用户只要提示词时以提示词为终点。无实际生图工具时标明能力缺口，不能用 HTML 或提示词冒充已出图。
- HTML 阅读／打印版仍可运行 `scripts/make_cards.py <episode_dir> --style G2`。

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

### ⑤ → 配音字幕视频（独立输出选项）

用户说「出配音视频」「图卡加配音」「带字幕短视频」时，读取 [narrated-video.md](narrated-video.md)：已核验的内容 → 短旁白 + 图卡 → 中文合成声音与词语时间 → 字幕与 MP4 → 验收。可以直接从本期逐字稿走完整链路，也可以复用已经完成的图卡。

`scripts/make_video.py` 是可复用的本地执行入口；图片使用当前生图工具，音频使用实际可用的语音服务。若用户指定生成模型的新动态场景，按 [codex-media.md](codex-media.md) 检查视频生成工具，不自动用图卡动画替代。

## 消费门槛

先运行本期 `verify_digest.py` 并核对必要的原稿和说话人；新摘要的信封由原脚本回写。复用旧摘要时，全局信封可能指向其他单集，不能只看全局状态。图片与配音视频另做内容、画面、字幕和音频检查，不把摘要机检当作媒体验收。
