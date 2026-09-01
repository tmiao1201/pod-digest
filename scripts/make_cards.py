#!/usr/bin/env python3
"""make_cards.py — 素材块① 分镜表 → 自包含 HTML 知识卡片册（图文结合，即看即转，零依赖）
用法: python3 scripts/make_cards.py <本期目录> [--style G1|G2|G3]
产物: 同目录 cards.html（3:4 卡片网格 + 风格预设配色；打印适配；后续生图提示词在 digest/独立文件）
"""
import argparse
import html
import json
import os
import re
import sys

STYLES = {
    "G1": {  # 手账笔记风
        "bg": "#faf6ec", "card": "#fffdf7", "ink": "#2b2b26", "accent": "#e8833a",
        "chip": "#eaf2fb", "chipink": "#2f6ea5", "font": "'Kaiti SC','STKaiti','KaiTi','PingFang SC',serif",
        "frame": "1.5px solid #cfe0f0", "hero_bg": "linear-gradient(transparent 62%, #ffe6b8 62%)",
        "texture": "repeating-linear-gradient(0deg,transparent,transparent 27px,#efe8d8 27px,#efe8d8 28px)",
    },
    "G2": {  # 扁平信息图
        "bg": "#f2f5f8", "card": "#ffffff", "ink": "#1a2332", "accent": "#e8833a",
        "chip": "#16405f", "chipink": "#ffffff", "font": "'PingFang SC','Microsoft YaHei',sans-serif",
        "frame": "1px solid #dde5ec", "hero_bg": "none", "texture": "none",
    },
    "G3": {  # 黑白编辑
        "bg": "#ececec", "card": "#ffffff", "ink": "#111111", "accent": "#b3261e",
        "chip": "#111111", "chipink": "#ffffff", "font": "'Songti SC','SimSun','PingFang SC',serif",
        "frame": "1px solid #111", "hero_bg": "none", "texture": "none",
    },
}


def parse_storyboard(digest_path):
    """解析素材块① 表格 → [(镜号, 画面内容, 文字要点)]"""
    s = open(digest_path, encoding="utf-8").read()
    seg = re.search(r"## 素材块①[^\n]*\n(.*?)(?=\n## |\Z)", s, re.S)
    if not seg:
        sys.exit("未找到素材块①")
    cards = []
    for line in seg.group(1).splitlines():
        line = line.strip()
        if not line.startswith("|") or re.match(r"^\|[\s\-:|]+\|$", line) or "镜号" in line:
            continue
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 3:
            cards.append((cells[0], cells[1], cells[2]))
    return cards


def hero_split(text):
    """文字要点 → (大标题, 副文)：按首个冒号/破折号断"""
    for sep in ("：", ":", "——", "—"):
        if sep in text:
            h, t = text.split(sep, 1)
            if 2 < len(h) < 20:
                return h.strip(), t.strip()
    m = re.match(r"(.{4,18}?)，(.+)", text)
    return (m.group(1), m.group(2)) if m else (text[:16], text)


def hl(t):
    t = html.escape(t)
    return re.sub(r"「([^」]+)」", r'<span class="hl">「\1」</span>', t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument("--style", default="G1", choices=list(STYLES))
    args = ap.parse_args()
    st = STYLES[args.style]
    cards = parse_storyboard(os.path.join(args.episode_dir, "digest.md"))
    meta = json.load(open(os.path.join(args.episode_dir, "meta.json"), encoding="utf-8"))
    title = open(os.path.join(args.episode_dir, "digest.md"), encoding="utf-8").readline().lstrip("# ").strip()

    deck = []
    for i, (no, visual, points) in enumerate(cards):
        hero, sub = hero_split(points)
        deck.append(f"""<div class="card">
<div class="top"><span class="chip">{html.escape(no)}</span><span class="src">{html.escape(meta.get('show',''))}</span></div>
<div class="hero">{hl(hero)}</div>
<div class="sub">{hl(sub)}</div>
<div class="brief"><span class="bl">🎬 画面脚本</span>{hl(visual)}</div>
</div>""")

    doc = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} · 知识卡片</title><style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:{st['font']};background:{st['bg']};color:{st['ink']};padding:28px 18px;line-height:1.6}}
.head{{max-width:1060px;margin:0 auto 20px}}
.head h1{{font-size:20px}} .head .meta{{font-size:12.5px;opacity:.65;margin-top:4px}}
.deck{{max-width:1060px;margin:0 auto;display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:18px}}
.card{{background:{st['card']};border:{st['frame']};border-radius:14px;padding:22px 20px 18px;
min-height:400px;display:flex;flex-direction:column;background-image:{st['texture']};
box-shadow:0 1px 5px rgba(20,35,55,.07)}}
.top{{display:flex;justify-content:space-between;align-items:center;margin-bottom:16px}}
.chip{{background:{st['chip']};color:{st['chipink']};border-radius:14px;padding:2px 13px;font-size:12.5px;letter-spacing:1px}}
.src{{font-size:11px;opacity:.5}}
.hero{{font-size:23px;font-weight:700;line-height:1.5;margin-bottom:10px;background-image:{st['hero_bg']};padding:0 2px}}
.sub{{font-size:14.5px;opacity:.92;margin-bottom:auto}}
.brief{{margin-top:18px;border-top:1px dashed {st['frame'].split(' ')[-1] if 'G' else '#ccc'};padding-top:12px;font-size:12.5px;opacity:.75}}
.bl{{display:block;font-size:11px;letter-spacing:2px;color:{st['accent']};margin-bottom:4px;font-weight:700}}
.hl{{color:{st['accent']};font-weight:700}}
.ft{{max-width:1060px;margin:22px auto 0;font-size:11px;opacity:.5;text-align:center}}
@media print{{body{{background:#fff}}.card{{box-shadow:none;break-inside:avoid}}}}
</style></head><body>
<div class="head"><h1>{html.escape(title)}</h1>
<div class="meta">{args.style} 风格预设 · {len(cards)} 张 · 3:4 · 由 pod-digest make_cards 生成 · 生图提示词见 digest 素材块①</div></div>
<div class="deck">{''.join(deck)}</div>
<div class="ft">卡片文字取自 digest 素材块①（证据分级见完整 digest） · 仅供学习分享</div>
</body></html>"""
    out = os.path.join(args.episode_dir, "cards.html")
    open(out, "w", encoding="utf-8").write(doc)
    print(f"✅ HTML 卡片册（{len(cards)} 张, {args.style}）→ {out}")


if __name__ == "__main__":
    main()
