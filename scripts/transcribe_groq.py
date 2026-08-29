#!/usr/bin/env python3
"""transcribe_groq.py — groq-direct 转写引擎：curl 直连 Groq Whisper API（multipart 原生支持）

原理: ffmpeg 转码为 16kHz 单声道 mp3 并按 15 分钟切段（Groq 免费档单文件约 25MB 上限）
      → 逐段 curl -F 上传 /openai/v1/audio/transcriptions (model=whisper-large-v3)
      → 每段返回 verbose_json（带 segment 时间戳）→ 偏移量修正后拼接为 [HH:MM:SS] 行

为什么用 curl 而不是 urllib：实测 python urllib 大 multipart 在部分网络下 Broken pipe
（curl 同链路稳定）；curl 为 macOS/Linux 标配，公域用户零额外依赖。

用法: transcribe_groq.py <audio_file> <out_txt> [--lang auto|zh|en|ja|...] [--model whisper-large-v3]
环境: GROQ_API_KEY 必须已设置（transcribe.sh 会自动从 agent-reach 的 config.yaml 借用）
"""
import argparse
import json
import os
import subprocess
import sys
import time

API = os.environ.get("GROQ_API_BASE", "https://api.groq.com/openai/v1").rstrip("/") \
    + "/audio/transcriptions"
SEGMENT_SEC = 900  # 15 分钟一段，48kbps 单声道 ≈ 5MB，远低于免费档 25MB 限制


def sh(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(cmd)}\n{r.stderr[-500:]}")
    return r.stdout


def probe_duration(path):
    out = sh(["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
              "-of", "csv=p=0", path])
    return float(out.strip())


def make_chunks(path, workdir):
    """转码 + 切段，返回按序排列的分段文件列表"""
    pattern = os.path.join(workdir, "chunk_%04d.mp3")
    sh(["ffmpeg", "-y", "-v", "error", "-i", path, "-ar", "16000", "-ac", "1",
        "-b:a", "48k", "-f", "segment", "-segment_time", str(SEGMENT_SEC),
        "-reset_timestamps", "1", pattern])
    return sorted(
        os.path.join(workdir, f) for f in os.listdir(workdir) if f.startswith("chunk_")
    )


def post_chunk(api_key, chunk, model, language):
    """curl 上传单段，返回 verbose_json dict；非 2xx / 网络错误抛 RuntimeError（含状态码）"""
    cmd = ["curl", "-s", "--max-time", "600", "--retry", "2",
           "-H", f"Authorization: Bearer {api_key}",
           "-F", f"model={model}",
           "-F", "response_format=verbose_json",
           "-F", "temperature=0"]
    if language and language != "auto":
        cmd += ["-F", f"language={language}"]
    cmd += ["-F", f"file=@{chunk}", "-w", "\n%{http_code}", API]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f"网络异常 curl exit={r.returncode}: {r.stderr.strip()[-200:]}")
    parts = r.stdout.rsplit("\n", 1)
    status = int(parts[1]) if len(parts) == 2 and parts[1].strip().isdigit() else 0
    body = parts[0]
    if status >= 400:
        raise RuntimeError(f"HTTP {status}: {body[:200]}")
    try:
        resp = json.loads(body)
    except json.JSONDecodeError:
        raise RuntimeError(f"非 JSON 响应: {body[:200]}")
    if "error" in resp:
        raise RuntimeError(f"API 错误: {str(resp['error'])[:200]}")
    return resp


def fmt_ts(sec):
    m, s = divmod(int(sec), 60)
    h, m = divmod(m, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("audio")
    ap.add_argument("out_txt")
    ap.add_argument("--lang", default="auto", help="auto=自动检测(默认)；可 zh/en/ja 等，建议英文播客填 en 提准")
    ap.add_argument("--model", default="whisper-large-v3")
    args = ap.parse_args()

    api_key = os.environ.get("GROQ_API_KEY", "")
    if not api_key:
        sys.exit("未设置 GROQ_API_KEY。注册 https://console.groq.com/keys 后 export GROQ_API_KEY=... "
                 "（本地若配了 agent-reach 可改用 transcribe.sh --engine agent-reach，key 委托它管）")

    total = probe_duration(args.audio)
    workdir = f"/tmp/pod-digest/chunks_{os.getpid()}"
    os.makedirs(workdir, exist_ok=True)
    print(f"音频 {total/60:.0f} 分钟 → 切段中...", file=sys.stderr)
    chunks = make_chunks(args.audio, workdir)
    print(f"共 {len(chunks)} 段，开始转写（model={args.model}, lang={args.lang}）", file=sys.stderr)

    lines = []
    for i, chunk in enumerate(chunks):
        offset = i * SEGMENT_SEC
        for attempt in range(3):  # 限频/网络抖动重试，超过即 Hard Stop
            try:
                resp = post_chunk(api_key, chunk, args.model, args.lang)
                break
            except RuntimeError as e:
                wait = 2**attempt * 8
                if attempt == 2:
                    sh(["rm", "-rf", workdir])
                    hint = "免费额度耗尽，稍后再试或换 agent-reach 引擎" if "429" in str(e) \
                        else "可换 --engine agent-reach，或检查网络/代理"
                    sys.exit(f"段 {i+1} 转写失败（{e}），已停。{hint}")
                print(f"段 {i+1} 失败，{wait}s 后重试（{attempt+1}/3）：{str(e)[:80]}", file=sys.stderr)
                time.sleep(wait)
        detected = resp.get("language", "?")
        for seg in resp.get("segments", []):
            ts = fmt_ts(seg["start"] + offset)
            text = seg["text"].strip()
            if text:
                lines.append(f"[{ts}] {text}")
        print(f"  段 {i+1}/{len(chunks)} 完成（检测语言: {detected}）", file=sys.stderr)
        time.sleep(1)  # 温和限频

    sh(["rm", "-rf", workdir])
    with open(args.out_txt, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"✅ 转写完成 → {args.out_txt}（{len(lines)} 段）", file=sys.stderr)


if __name__ == "__main__":
    main()
