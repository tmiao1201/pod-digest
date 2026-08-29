#!/usr/bin/env python3
"""transcribe_groq.py — groq-direct 转写引擎：纯 stdlib 直连 Groq Whisper API，零非标依赖

原理: ffmpeg 转码为 16kHz 单声道 mp3 并按 15 分钟切段（Groq 免费档单文件约 25MB 上限）
      → 逐段 POST /openai/v1/audio/transcriptions (model=whisper-large-v3)
      → 每段返回 verbose_json（带 segment 时间戳）→ 偏移量修正后拼接为 [MM:SS] 行

用法: transcribe_groq.py <audio_file> <out_txt> [--lang auto|zh|en|ja|...] [--model whisper-large-v3]
环境: GROQ_API_KEY 必须已设置（免费注册 https://console.groq.com/keys）
"""
import argparse
import json
import mimetypes
import os
import subprocess
import sys
import time
import urllib.request
import uuid

API = "https://api.groq.com/openai/v1/audio/transcriptions"
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
    """multipart/form-data 上传单段，返回 verbose_json dict"""
    boundary = uuid.uuid4().hex
    fields = {"model": model, "response_format": "verbose_json", "temperature": "0"}
    if language and language != "auto":
        fields["language"] = language

    body = bytearray()
    for k, v in fields.items():
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"{k}\"\r\n\r\n{v}\r\n").encode()
    mime = mimetypes.guess_type(chunk)[0] or "audio/mpeg"
    fname = os.path.basename(chunk)
    body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"file\"; "
             f"filename=\"{fname}\"\r\nContent-Type: {mime}\r\n\r\n").encode()
    with open(chunk, "rb") as f:
        body += f.read()
    body += f"\r\n--{boundary}--\r\n".encode()

    req = urllib.request.Request(
        API, data=bytes(body), method="POST",
        headers={"Authorization": f"Bearer {api_key}",
                 "Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return json.loads(r.read())


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
            except urllib.error.HTTPError as e:
                wait = 2**attempt * 5
                if attempt == 2:
                    sh(["rm", "-rf", workdir])
                    sys.exit(f"段 {i+1} 转写失败（{e.code} {e.reason}），已停。"
                             f"429=免费额度耗尽，稍后再试或换 agent-reach 引擎")
                print(f"段 {i+1} 失败({e.code})，{wait}s 后重试", file=sys.stderr)
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
