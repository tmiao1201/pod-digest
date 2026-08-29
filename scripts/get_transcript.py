#!/usr/bin/env python3
"""get_transcript.py — 主入口：播客名/RSS链接 → 单集音频下载 → 带时间戳 transcript.txt

用法:
  get_transcript.py "硅谷101" --match Moderna            # 按标题关键词选集
  get_transcript.py "硅谷101" --latest                    # 最新一期
  get_transcript.py "https://feeds.fireside.fm/sv101/rss" --match E250
  可选: --lang zh|en|auto（转写语言提示，默认auto）
        --engine auto|agent-reach|groq-direct
        --keep-audio（保留下载的音频，默认转写完即删）
        --youtube <URL>（该集有YouTube版：直接抓字幕，跳过音频+转写）

产物: out/episodes/<show>/<yyyymmdd>-<slug>/{meta.json, transcript.txt}
幂等: transcript.txt 已存在则跳过下载转写，直接报路径
"""
import argparse
import json
import os
import re
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone

DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DIR)
OUT_ROOT = os.path.join(ROOT, "out", "episodes")
TMP = "/tmp/pod-digest"


def sh(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError(f"命令失败: {' '.join(map(str, cmd))}\n{r.stderr[-800:]}")
    return r.stdout


def slugify(text, maxlen=48):
    s = re.sub(r"[^\w一-鿿]+", "-", text).strip("-")
    return s[:maxlen].rstrip("-") or "untitled"


def resolve_feed(name_or_url):
    if name_or_url.startswith("http://") or name_or_url.startswith("https://"):
        return name_or_url, None
    out = sh(["bash", os.path.join(DIR, "itunes_search.sh"), name_or_url])
    lines = [l for l in out.strip().splitlines() if "|" in l]
    if not lines:
        raise RuntimeError(f"iTunes 未找到「{name_or_url}」的 RSS")
    print("候选节目:", file=sys.stderr)
    for i, l in enumerate(lines):
        print(f"  [{i}] {l.split(' | ')[0]}", file=sys.stderr)
    # 多个候选时取名字与输入最接近的（完全包含优先），并提示
    name_low = name_or_url.lower()
    pick = next((l for l in lines if l.split(" | ")[0].lower() == name_low), None)
    if not pick:
        pick = next((l for l in lines if name_low in l.split(" | ")[0].lower() or
                     l.split(" | ")[0].lower() in name_low), lines[0])
    feed = pick.split(" | ")[1]
    print(f"选中: {pick.split(' | ')[0]} → {feed}", file=sys.stderr)
    return feed, pick.split(" | ")[0]


def select_episode(feed, match, latest):
    cmd = ["python3", os.path.join(DIR, "parse_feed.py"), feed, "--json"]
    if latest:
        cmd += ["--latest"]
    elif match:
        cmd += ["--match"] + match
    else:
        cmd += ["--latest"]
        print("未指定 --match，默认取最新一期（--list 可先看集数）", file=sys.stderr)
    return json.loads(sh(cmd))


def download_audio(url, dest):
    req = urllib.request.Request(url, headers={"User-Agent": "pod-digest/0.1"})
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        while True:
            buf = r.read(1 << 20)
            if not buf:
                break
            f.write(buf)
    return dest


def yt_cookie_args():
    """YouTube 反爬需要登录态 cookie。
    默认: 装了 Chrome 就用 chrome 的（用户多半登录着 YouTube）
    覆盖: PODDIGEST_YT_COOKIES=firefox/safari/none 或 --yt-cookies 参数"""
    override = os.environ.get("PODDIGEST_YT_COOKIES", "")
    if override:
        return [] if override == "none" else ["--cookies-from-browser", override]
    if os.path.exists("/Applications/Google Chrome.app"):
        return ["--cookies-from-browser", "chrome"]
    return []


def youtube_subs(url, out_dir, yt_cookies=None):
    """抓 YouTube 字幕作为逐字稿（自动字幕通常无标点，digest 引擎可处理）"""
    sub_prefix = os.path.join(out_dir, "sub")
    sh(["yt-dlp", "--skip-download", "--write-sub", "--write-auto-sub",
        "--sub-langs", "zh-Hans,zh,en.*,ja.*,default", "--convert-subs", "vtt",
        *yt_cookie_args(), "-o", sub_prefix, url])
    found = [f for f in os.listdir(out_dir) if f.startswith("sub") and f.endswith(".vtt")]
    if not found:
        raise RuntimeError("YouTube 无字幕文件（或被反爬拦截）→ 改走音频转写路径")

    # 字幕轨择优: 原创中文 > 原创外文 > 机器翻译轨（形如 en-zh-Hans = 从zh-Hans机翻成英文）
    ZH = {"zh-Hans", "zh-CN", "zh", "zh-Hant", "zh-TW", "zh-HK"}

    def track_rank(f):
        lang = f[len("sub."):-len(".vtt")]
        if lang in ZH:
            return 0
        if re.match(r"^[a-z]{2}-", lang):
            return 2  # 机翻轨（目标语-源语）
        return 1      # 原创外文
    vtt = os.path.join(out_dir, sorted(found, key=lambda f: (track_rank(f), f))[0])
    # vtt → [HH:MM:SS] 行（去重复行/头）
    lines, seen = [], set()
    for ln in open(vtt, encoding="utf-8", errors="ignore"):
        ln = ln.strip()
        m = re.match(r"^(\d{2}:\d{2}:\d{2})\.\d{3}", ln)
        if m:
            last_ts = m.group(1)
            continue
        if ln and not ln.startswith(("--", "WEBVTT", "Kind:", "Language:")):
            text = re.sub(r"<[^>]+>", "", ln)
            if text and text not in seen:
                seen.add(text)
                lines.append(f"[{last_ts}] {text}")
    with open(os.path.join(out_dir, "transcript.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return len(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("source", help="播客名 或 RSS 链接")
    ap.add_argument("--match", nargs="+", metavar="关键词")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--lang", default="auto")
    ap.add_argument("--engine", default="auto")
    ap.add_argument("--keep-audio", action="store_true")
    ap.add_argument("--youtube", metavar="URL", help="该集 YouTube 版链接，抓字幕免转写")
    args = ap.parse_args()

    os.makedirs(TMP, exist_ok=True)
    feed, show_name = resolve_feed(args.source)
    ep = select_episode(feed, args.match, args.latest)

    show = slugify(show_name or ep["show"])
    date = (ep.get("pubdate") or "")[:16].replace(" ", "")
    m = re.match(r"\w{3},\s*(\d{2})\s*(\w{3})\s*(\d{4})", ep.get("pubdate") or "")
    months = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
    if m:
        date = f"{m.group(3)}{months.index(m.group(2)) + 1:02d}{m.group(1)}"
    ep_slug = slugify(ep["title"], 48)
    out_dir = os.path.join(OUT_ROOT, show, f"{date or 'unknown'}-{ep_slug}")
    os.makedirs(out_dir, exist_ok=True)
    transcript = os.path.join(out_dir, "transcript.txt")

    if os.path.exists(transcript):
        print(f"✅ 已存在，跳过: {transcript}")
        return

    meta = {**ep, "feed": feed, "fetched_at": datetime.now(timezone.utc).isoformat(),
            "out_dir": out_dir, "engine": args.engine}
    with open(os.path.join(out_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print(f"📁 {out_dir}", file=sys.stderr)

    if args.youtube:
        n = youtube_subs(args.youtube, out_dir)
        print(f"✅ YouTube 字幕逐字稿（{n} 行）→ {transcript}")
        return

    if not ep.get("audio_url"):
        raise RuntimeError("该集 RSS 无音频 enclosure（可能是付费/独家），改用 --youtube 或手动提供音频")

    ext = os.path.splitext(ep["audio_url"].split("?")[0])[1] or ".mp3"
    audio = os.path.join(TMP, f"{ep_slug}{ext}")
    if os.path.exists(audio) and (not ep["audio_bytes"]
                                  or abs(os.path.getsize(audio) - ep["audio_bytes"]) < 1e6):
        print(f"♻️  复用已有音频: {audio}", file=sys.stderr)
    else:
        print(f"⬇️  下载音频 {ep['audio_bytes'] / 1e6:.0f}MB ...", file=sys.stderr)
        download_audio(ep["audio_url"], audio)

    print(f"🎙️  转写中（引擎 {args.engine}, 语言 {args.lang}）...", file=sys.stderr)
    sh(["bash", os.path.join(DIR, "transcribe.sh"), audio, transcript,
        "--engine", args.engine, "--lang", args.lang])
    if not args.keep_audio:
        os.remove(audio)
    print(f"✅ 逐字稿 → {transcript}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ {e}", file=sys.stderr)
        sys.exit(1)
