#!/usr/bin/env python3
"""parse_feed.py — 解析播客 RSS：列集数 / 按关键词选集 / 导出单集元数据+音频地址

用法:
  parse_feed.py <feed_url或本地xml> --list [N]          # 列最近 N 集（默认 15）
  parse_feed.py <feed...> --match "Moderna"             # 按标题关键词选集（可多个词，空格分隔，全部命中优先，任一命中次之）
  parse_feed.py <feed...> --latest                      # 直接取最新一期
  parse_feed.py <feed...> --match "E250" --json         # 输出 JSON（供 meta.json）

输出 JSON 字段: show/title/pubdate/duration_sec/audio_url/audio_bytes/episode_link/shownotes/feed
时长统一换算成秒（RSS 里 itunes:duration 可能是 秒 或 HH:MM:SS 两种格式，都处理）
"""
import argparse
import json
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

NS = {"itunes": "http://www.itunes.com/dtds/podcast-1.0.dtd"}


def dur_to_sec(text):
    """RSS itunes:duration 兼容 '4600' / '1:16:50' / '16:50' 三种写法"""
    if not text:
        return None
    text = text.strip()
    if re.fullmatch(r"\d+", text):
        return int(text)
    parts = text.split(":")
    try:
        return sum(int(p) * 60**i for i, p in enumerate(reversed(parts)))
    except ValueError:
        return None


def load_feed(source):
    if source.startswith("http://") or source.startswith("https://"):
        req = urllib.request.Request(source, headers={"User-Agent": "pod-digest/0.1"})
        with urllib.request.urlopen(req, timeout=30) as r:
            return ET.fromstring(r.read())
    return ET.parse(source).getroot()


def parse_items(root):
    ch = root.find("channel")
    if ch is None:
        raise SystemExit("不是合法的 RSS（无 channel）")
    items = []
    for it in ch.findall("item"):
        enc = it.find("enclosure")
        dur = it.find("itunes:duration", NS)
        items.append({
            "title": (it.findtext("title") or "").strip(),
            "pubdate": (it.findtext("pubDate") or "").strip(),
            "duration_sec": dur_to_sec(dur.text if dur is not None else None),
            "audio_url": enc.get("url") if enc is not None else None,
            "audio_bytes": int(enc.get("length") or 0) if enc is not None else 0,
            "episode_link": (it.findtext("link") or "").strip(),
            "shownotes": (it.findtext("description") or "").strip(),
        })
    return (ch.findtext("title") or "").strip(), items  # RSS 按发布序，items[0] 最新


def pick(items, keywords):
    """多关键词：全部命中最优，其次任一命中，按 RSS 顺序（新→旧）取第一个"""
    kws = [k.lower() for k in keywords]
    all_hit = any_hit = None
    for it in items:
        t = it["title"].lower()
        if all(k in t for k in kws):
            all_hit = it
            break
        if any_hit is None and any(k in t for k in kws):
            any_hit = it
    return all_hit or any_hit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("feed")
    ap.add_argument("--list", nargs="?", type=int, const=15, default=None, metavar="N")
    ap.add_argument("--match", nargs="+", metavar="关键词")
    ap.add_argument("--latest", action="store_true")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    root = load_feed(args.feed)
    show, items = parse_items(root)

    if args.list is not None:
        for it in items[: args.list]:
            m, s = divmod(it["duration_sec"] or 0, 60)
            h, m = divmod(m, 60)
            dur = f"{h}h{m:02d}m" if h else f"{m}m"
            print(f"{it['pubdate'][:16]:16s} | {dur:>6s} | {it['title']}")
        print(f"-- 共 {len(items)} 集，频道: {show}")
        return

    ep = None
    if args.match:
        ep = pick(items, args.match)
        if not ep:
            print(f"标题无命中关键词: {args.match}。用 --list 看集数列表", file=sys.stderr)
            sys.exit(1)
    elif args.latest:
        ep = items[0]

    if not ep:
        print("需指定 --match 关键词 / --latest / --list", file=sys.stderr)
        sys.exit(1)

    out = {"show": show, **ep, "feed": args.feed}
    if args.json:
        print(json.dumps(out, ensure_ascii=False, indent=1))
    else:
        m, s = divmod(ep["duration_sec"] or 0, 60)
        h, m = divmod(m, 60)
        print(f"频道: {show}")
        print(f"标题: {ep['title']}")
        print(f"发布: {ep['pubdate']}  时长: {h}h{m:02d}m{s:02d}s")
        print(f"音频: {ep['audio_url']}")
        print(f"大小: {ep['audio_bytes'] / 1e6:.0f} MB")
        print(f"页面: {ep['episode_link']}")


if __name__ == "__main__":
    main()
