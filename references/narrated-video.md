# 配音字幕视频

用于「出配音视频」「图卡加配音」「做成带字幕短视频」。交付的是中文旁白配图卡动效的实际 MP4；生成模型的新动态场景需要另有可用的视频工具。

## 内容与节奏

1. 复用本期逐字稿、摘要与来源记录，逐段回对。保留观点归属、数字口径和研究阶段，医学内容保留临床终点与结果限制。
2. 将内容改写成适合朗读的短旁白。普通话一分钟可先按约 200–250 字起草，最终以实际语音时长为准；需要更短时精简内容，不靠过度加速。旁白是编辑转述，不标成嘉宾原话。
3. 每段对应一张图卡。沿用已有合格图片，或按 [codex-media.md](codex-media.md) 实际生图。默认使用不透明图片；脚本按原比例放入画布，不拉伸图片。
4. 采用当前可用的合成声音，不冒充节目原声。默认示例为普通话女声，可按用户偏好更换；画面带「AI 配音」标记。

只请求摘要或静态图片时不自动调用配音服务。无需为了每张卡、每段旁白重复询问已明确的输出选择。

## 可复用入口

在项目根目录运行 `scripts/make_video.py`。环境需要：

- Python 3.10+；可选依赖见 `requirements-video.txt`，不影响原来的摘要／报告脚本。
- 系统 FFmpeg 和 ffprobe；需有 libx264、zoompan、xfade、overlay、loudnorm。
- 可用中文 TTF/TTC 字体。自动检查常见 macOS、Linux 和 Windows 字体路径；找不到时用 `--font` 指定。项目不分发系统字体。

默认通过 [edge-tts](https://github.com/rany2/edge-tts) 调用 Microsoft Edge 在线语音服务，无需独立 API key；会发送旁白文本，需要联网。当前音色列表可通过 `uv run --with-requirements requirements-video.txt edge-tts --list-voices` 查询。实际可用性以服务响应为准；失败保留日志，不将分镜或无声视频标成配音成功。

也可先在现有虚拟环境安装 `python -m pip install -r requirements-video.txt`，然后直接运行脚本。不要为了视频修改其他工具的全局依赖。

## 输入 narration.json

最小输入是 `scenes`；可选 `label`、`voice`、`rate`，以及来源字段。图卡路径相对于 JSON 所在目录解析，也接受绝对路径。每段 `id` 为唯一正整数，省略时按顺序补齐。

```json
{
  "label": "硅谷101 E250",
  "source_url": "https://sv101.fireside.fm/263",
  "voice": "zh-CN-XiaoxiaoNeural",
  "rate": "+3%",
  "scenes": [
    {
      "id": 1,
      "image": "cards/card-02.png",
      "text": "个性化肿瘤疫苗先筛选新抗原，再编码成 mRNA，教免疫系统识别肿瘤。",
      "source": {
        "timestamp": "14:09",
        "precision": "章节起点",
        "claim_type": "节目机制讲解的编辑转述"
      }
    }
  ]
}
```

完整示例见 [narration-example.json](../examples/narration-example.json)。示例不附实际图卡，运行前换成当前任务的图片和旁白。还应在输入中保存 `source_evidence`／`source_review` 指向本期证据与人工核验记录，或在每段 `source` 中保存原稿路径、片段、说话人和时间精度。脚本保留这些字段，但不会自动验证科学事实。

## 执行

```bash
# 只检查输入、图片、字体和本地依赖；不联网、不创建输出
uv run --with-requirements requirements-video.txt python scripts/make_video.py \
  out/my-episode/narration.json --out out/my-episode/video-01 --check-only

# 实际配音、合成、技术检查
uv run --with-requirements requirements-video.txt python scripts/make_video.py \
  out/my-episode/narration.json --out out/my-episode/video-01

# 同一旁白只改画面：音频复用，不重复调用配音服务
uv run --with-requirements requirements-video.txt python scripts/make_video.py \
  out/my-episode/narration.json --out out/my-episode/video-02 \
  --reuse-audio out/my-episode/video-01
```

`--out` 必须是新目录，脚本拒绝覆盖，包括已存在的空目录。可用 `--voice`、`--rate`、`--font` 覆盖默认值；负语速写成 `--rate=-5%`。复用时核对旁白文字、顺序、音色与语速，并重新检查词语时间与音频长度，不能给改过的旁白配旧声音。

脚本不自行重试整个生成任务。配音或合成失败时保留已完成的素材、日志和 `error.json`，按主技能的失败纪律处理；确认有效素材后再在新目录继续。

## 产物与验收

输出目录包含：

- `video.mp4`：1080 × 1920、30 fps、H.264 视频和 AAC 配音；字幕已烧录进画面。
- `narration.m4a`、`narration.wav`：独立音轨；另保留分段配音与词语时间。
- `subtitles.srt`、`narration.md`、`narration.json`：字幕、文稿及完整来源输入。
- `video-manifest.json`：画面、语音、字幕时间与生成方式。
- `verification.json`、`qa-scene-*.jpg`：技术检查和每段的抽帧图。

技术检查包括音视频流、时长、帧率、完整解码、黑帧区间与音量；字幕与配音词语时间做内容勾稽。脚本会明确留下 `visual_review=pending`，不自动宣称视觉、听感或事实已验证。

交付前逐张查看实际抽帧，确认图卡、字幕、来源可读，字幕不遮挡正文；具备音频输入或播放检查条件时，再检查中文专名、英文缩写、停顿和音画同步。不具备听感验收条件时，在检查记录中如实标明，不能声称已试听。实际人工结果另存 `review.md`，保留脚本的检查证据。

最终展示实际 MP4 并链接成品，简要标明时长、配音和字幕。只生成文件不等于已经发布到任何平台；发布按用户单独授权执行。
