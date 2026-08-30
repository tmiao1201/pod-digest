#!/usr/bin/env python3
"""scan_watchlist.py — 扫订阅清单：每个节目最新一集 + 是否已 digest（v1 只列不自动跑）

用法: scan_watchlist.py            # 全部节目
      scan_watchlist.py 硅谷101    # 单个节目
输出: 每行 "节目 | 最新集标题 | 状态(🟢已digest/⚪未digest/🔴feed失败)"
依赖: 零（shows.yaml 用内置简易解析，schema 固定：name/itunes_name/youtube/rss/lang/tags）
"""
import os
import re
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(DIR)
SHOWS = os.path.join(ROOT, "config", "shows.yaml")
OUT_EP = os.path.join(ROOT, "out", "episodes")


def parse_shows(path):
    """解析自家固定 schema 的 yaml（不引入 pyyaml 依赖）"""
    shows, cur = [], None
    for line in open(path, encoding="utf-8"):
        if re.match(r"^\s*-\s+name:\s*(.+)$", line):
            cur = {"name": re.match(r"^\s*-\s+name:\s*(.+)$", line).group(1).strip()}
            shows.append(cur)
        elif cur:
            m = re.match(r"^\s+(\w+):\s*(.*)$", line)
            if m and m.group(1) in ("itunes_name", "youtube", "rss", "lang"):
                cur[m.group(1)] = m.group(2).strip().strip('"')
    return shows


def main():
    shows = []
    for path in (SHOWS, os.path.join(os.path.dirname(SHOWS), "shows.local.yaml")):
        if os.path.exists(path):
            shows += parse_shows(path)   # 示例清单 + 个人私单(shows.local.yaml, 不入库)
    seen, uniq = set(), []
    for s_ in shows:                     # 按 name 去重（local 覆盖示例同名条目）
        if s_["name"] not in seen:
            seen.add(s_["name"]); uniq.append(s_)
    shows = uniq
    if len(sys.argv) > 1:
        shows = [s for s in shows if sys.argv[1] in s["name"]]

    sys.path.insert(0, DIR)
    from parse_feed import load_feed, parse_items  # 复用分步工具
    from get_transcript import slugify

    for s in shows:
        try:
            feed = s.get("rss")
            if not feed:
                import subprocess
                out = subprocess.run(["bash", os.path.join(DIR, "itunes_search.sh"),
                                      s.get("itunes_name") or s["name"]],
                                     capture_output=True, text=True)
                lines = [l for l in out.stdout.splitlines() if "|" in l]
                if not lines:
                    raise RuntimeError(out.stderr.strip().splitlines()[-1] if out.stderr else "feed 未找到")
                feed = lines[0].split(" | ")[1]
            _, items = parse_items(load_feed(feed))
            latest = items[0]
            show_dir = os.path.join(OUT_EP, slugify(s["name"]))
            done = False
            if os.path.isdir(show_dir):
                for d in os.listdir(show_dir):
                    if os.path.exists(os.path.join(show_dir, d, "digest.md")):
                        done = True  # 粗粒度：目录里有 digest 即算（精确版按标题匹配，v2 再做）
            mark = "🟢" if done else "⚪"
            m = (latest["duration_sec"] or 0) // 60
            print(f"{mark} {s['name']} | {latest['title'][:52]} | {m}分钟 | {latest['pubdate'][:16]}")
        except Exception as e:
            print(f"🔴 {s['name']} | feed 失败: {str(e)[:60]}")
    print("（🟢已digest ⚪未digest 🔴失败；对某集跑: python3 scripts/get_transcript.py \"<节目名>\" --latest）")


if __name__ == "__main__":
    main()
