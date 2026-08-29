# 本地私设（Ted 的环境）—— 发布公域时本文件整体替换为通用安装指引

> 公域原则：主流程（SKILL.md / scripts / 其他 references）不出现任何本机路径和私有依赖，
> 全部收拢在这里。

## 环境

- 机器：MacBook M3 / 16GB，macOS
- 开发仓：`~/cc/pod-digest`，symlink：`~/.claude/skills/pod-digest -> ~/cc/pod-digest`
- yt-dlp / ffmpeg：brew 安装（`/opt/homebrew/bin/`）
- YouTube 字幕路径需要：新版 yt-dlp（YouTube 反爬更新频繁，跑不动就 `brew upgrade yt-dlp`）
  + Chrome 登录态 cookie（`--cookies-from-browser chrome`）

## 转写引擎

- agent-reach CLI：`~/.local/bin/agent-reach`
- groq key 托管：`agent-reach configure groq-key <key>`（key 不进任何 .env/zshrc）
- 状态检查：`agent-reach doctor --json` 看 youtube / xiaoyuzhou 后端
- 未装 agent-reach 的回退：`export GROQ_API_KEY=...`（groq-direct 引擎）

## chain-rotation 数据层（素材块② data_source=local-tsdata 时）

- `PYTHONPATH=/Users/tedmiao/cursor /usr/local/bin/python3`
- `tsdata.get_panel` / `tsdata.get_fina` / `report_rc`（详见 chain-rotation skill 的 references/data_layer.md）
- 数据新鲜度落后 > 2 交易日先 `tsdata.update`

## Obsidian 第二大脑

- vault 在 iCloud；digest 存入brain 的捕获目录由用户当次指定（无固定路径）

## 工作台信封

- 外壳：`~/cursor/workbench/build.py`（REGISTRY 注册表）
- 本 skill 信封：`out/envelopes/pod-digest.json`（未来在 REGISTRY 加一行即可入动物园外壳）
