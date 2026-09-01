#!/usr/bin/env python3
"""make_report.py — digest.md → 自包含 HTML 研究简报（零依赖，公域内置下游③「出报告」）
用法: python3 scripts/make_report.py out/episodes/<show>/<dir>/   → 同目录 report.html
设计: 只解析 pod-digest 自家 digest 模板结构（板块固定），不追求通用 markdown
"""
import html
import json
import os
import re
import sys

BADGE = {"🟢": ("g", "有数据支撑"), "🟡": ("y", "单一口述"), "🔴": ("r", "利益相关")}


def inline(t):
    t = html.escape(t)
    t = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    # 证据徽章
    for k, (cls, _) in BADGE.items():
        t = t.replace(k, f'<span class="bdg {cls}">{k}</span>')
    t = re.sub(r"「([^」]+)」", r'<span class="q">「\1」</span>', t)
    return t


def render(digest_path):
    lines = open(digest_path, encoding="utf-8").read().splitlines()
    out, i = [], 0
    in_table, table_rows = False, []
    in_meta = False

    def flush_table():
        nonlocal table_rows, in_table
        if table_rows:
            out.append('<table>')
            for ri, row in enumerate(table_rows):
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                tag = "th" if ri == 0 or set(row) <= set("|-: ") else "td"
                out.append("<tr>" + "".join(f"<{tag}>{inline(c)}</{tag}>" for c in cells) + "</tr>")
            out.append("</table>")
        table_rows, in_table = [], False

    while i < len(lines):
        l = lines[i]
        if l.strip().startswith("|"):
            in_table = True
            if not re.match(r"^\|[\s\-:|]+\|$", l.strip()):
                table_rows.append(l)
            i += 1
            continue
        if in_table:
            flush_table()
        if l.startswith("# ") and not out:
            out.append(f'<h1 class="title">{inline(l[2:])}</h1>')
        elif l.startswith("## "):
            sec = l[3:].strip()
            if sec.startswith(("素材块", "附录")):
                out.append(f'<h2 class="sub">{inline(sec)}</h2>')
            else:
                out.append(f"<h2>{inline(sec)}</h2>")
        elif l.startswith("**") and l.endswith("**") and len(l) < 60:
            out.append(f'<div class="grouph">{inline(l)}</div>')
        elif l.startswith("> "):
            out.append(f'<div class="meta">{inline(l[2:])}</div>')
        elif re.match(r"^\s*-\s+", l):
            depth = (len(l) - len(l.lstrip())) // 2
            out.append(f'<div class="li d{min(depth,2)}">{inline(l.lstrip()[2:])}</div>')
        elif re.match(r"^\s*\d+\.\s+", l):
            out.append(f'<div class="li d0">{inline(re.sub(r"^\\d+\\.\\s+", "", l.lstrip()))}</div>')
        elif l.strip() == "---":
            out.append("<hr>")
        elif l.strip():
            out.append(f"<p>{inline(l)}</p>")
        i += 1
    if in_table:
        flush_table()
    return "\n".join(out)


CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:"PingFang SC","Microsoft YaHei",sans-serif;background:#eef1f5;color:#1a2332;line-height:1.75;font-size:15px}
.page{max-width:900px;margin:24px auto;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 2px 12px rgba(13,33,55,.08)}
header{background:linear-gradient(135deg,#0d2137,#16405f);color:#fff;padding:34px 40px 26px}
.title{font-size:23px;line-height:1.45;letter-spacing:.3px}
.meta{background:rgba(255,255,255,.07);border-left:3px solid #e8a33d;border-radius:0 8px 8px 0;padding:10px 14px;margin-top:12px;font-size:13.5px;opacity:.95}
main{padding:30px 40px 40px}
h2{font-size:17.5px;color:#0d2137;border-left:4px solid #2f6ea5;padding-left:10px;margin:30px 0 12px}
h2.sub{border-color:#8494a5;color:#44536a;font-size:15.5px}
.grouph{font-weight:700;color:#2f6ea5;font-size:14px;margin:16px 0 8px}
.li{padding:3px 0 3px 18px;position:relative;font-size:14px}
.li:before{content:"";position:absolute;left:2px;top:13px;width:6px;height:6px;border-radius:50%;background:#2f6ea5;opacity:.55}
.li.d1{padding-left:34px;font-size:13px;color:#44536a}.li.d1:before{left:18px;background:#8494a5}
.li.d2{padding-left:50px;font-size:12.5px;color:#5b6b7d}.li.d2:before{left:34px;background:#b9c6d3}
p{margin:8px 0;font-size:14px}
.bdg{display:inline-block;padding:0 7px;border-radius:11px;font-size:11.5px;margin:0 2px;vertical-align:1px}
.bdg.g{background:#e3f2e8;color:#1e6b3a}.bdg.y{background:#faf3df;color:#8a6410}.bdg.r{background:#fbe4dd;color:#a33d1e}
.q{background:#f2f6fa;padding:0 3px;border-radius:4px}
code{background:#f0f3f7;padding:1px 6px;border-radius:4px;font-size:12.5px;color:#0d5c8a}
table{width:100%;border-collapse:collapse;font-size:12.8px;margin:10px 0}
th{background:#0d2137;color:#fff;padding:7px 9px;text-align:left;font-weight:500}
td{padding:7px 9px;border-bottom:1px solid #e8edf2;vertical-align:top}
tr:nth-child(even) td{background:#f8fafc}
hr{border:none;border-top:1px dashed #c6d1dc;margin:22px 0}
footer{background:#f4f6f9;padding:16px 40px;font-size:11.5px;color:#8494a5;line-height:1.6}
@media print{body{background:#fff}.page{box-shadow:none;margin:0;border-radius:0}}
"""


def main():
    episode_dir = sys.argv[1].rstrip("/")
    digest = os.path.join(episode_dir, "digest.md")
    body = render(digest)
    meta = json.load(open(os.path.join(episode_dir, "meta.json"), encoding="utf-8"))
    title = open(digest, encoding="utf-8").readline().lstrip("# ").strip()
    footer = (f"来源播客：{meta.get('show','')}（{meta.get('pubdate','')[:16]}）· 由 pod-digest 生成 · "
              f"证据分级 🟢有数据/🟡单一口述/🔴利益相关 · 转写可能有误转（见 digest 附录对照表） · "
              f"仅供研究学习，非投资建议")
    doc = f"""<!DOCTYPE html><html lang="zh"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><style>{CSS}</style></head><body>
<div class="page"><header><h1 class="title">{html.escape(title)}</h1></header>
<main>{body}</main><footer>{footer}</footer></div></body></html>"""
    out = os.path.join(episode_dir, "report.html")
    open(out, "w", encoding="utf-8").write(doc)
    print(f"✅ 报告 → {out}")


if __name__ == "__main__":
    main()
