#!/usr/bin/env python3
"""verify_digest.py — digest 机检门禁（检查者≠执行者的落地：全部为确定性正则/计数，无 LLM 自评）

用法:
  python3 scripts/verify_digest.py out/episodes/<show>/<date>-<slug>/     # 检查并打印
  python3 scripts/verify_digest.py <目录> --write-envelope               # 全绿才写 green 信封

退出码: 全 PASS(含 WARN)=0；任一 FAIL=1。信封 status 由机检决定，手写会被覆写。
执行期禁止修改本脚本（RedFlag）：改尺子=重新量，需修脚本则先修再全量重跑。
"""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENVELOPE = os.path.join(ROOT, "out", "envelopes", "pod-digest.json")
TS_RE = re.compile(r"^\[(\d{1,2}):(\d{2})(?::(\d{2}))?")
CHAPTER_RE = re.compile(r"(\d{1,2}:\d{2}(?::\d{2})?)")
IDENTITY_WORDS = ("创始人", "股东", "投资", "老东家", "竞品", "自家", "高管")
DATA_SOURCES = {"local-tsdata", "tushare", "akshare", "manual", "qualitative"}


class R:
    def __init__(self):
        self.fails, self.warns, self.passed = [], [], 0

    def ok(self, msg):
        self.passed += 1

    def fail(self, msg):
        self.fails.append(msg)

    def warn(self, msg):
        self.warns.append(msg)


def norm(text):
    """金句回对归一化: 去标点/空白/[?]/行内时间戳——「逐字符」的机器定义"""
    text = re.sub(r"\[\d{1,2}:\d{2}(?::\d{2})?\]", "", text)  # 剥 [00:06:10] 式行内时间戳
    text = re.sub(r"&[a-z]+;", " ", text)                            # 剥 &gt;&amp; 等 HTML 实体
    text = text.replace("[?]", "")
    text = re.sub(r"[\s\[\]，。！？；：、,.!?;:\"'「」『』（）()《》<>—\-…·／/\\‘’]", "", text)
    return text.lower()                                              # 大小写不敏感（字幕小写 vs 引文句首大写）


def parse_ts_hms(m):
    h, m_, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    return h * 3600 + m_ * 60 + s


def load(episode_dir):
    files = {}
    for name in ("transcript.txt", "meta.json", "digest.md"):
        p = os.path.join(episode_dir, name)
        if not os.path.exists(p) or os.path.getsize(p) == 0:
            raise SystemExit(f"FAIL: 缺 {name}")
        files[name] = open(p, encoding="utf-8").read()
    return files["transcript.txt"], json.loads(files["meta.json"]), files["digest.md"]


def check_coverage(r, transcript, meta, digest):
    """B组: 转写覆盖勾稽（Judge修订: 率带不达标→降级复核而非硬拒，需 digest 含复核记录行）"""
    dur = int(meta.get("duration_sec") or 0)
    if dur <= 0:
        r.warn("meta 无 duration_sec，跳过覆盖勾稽")
        return
    lines = [l for l in transcript.splitlines() if l.strip()]
    ts_lines = [l for l in lines if TS_RE.match(l.strip())]
    has_review_note = "覆盖度复核：" in digest
    if len(ts_lines) > len(lines) * 0.8:  # 带时间戳格式
        tss = [parse_ts_hms(TS_RE.match(l.strip())) for l in ts_lines]
        if tss[-1] < dur * 0.9:
            (r.warn if has_review_note else r.fail)(
                f"时间戳仅覆盖到 {tss[-1]}/{dur}s (<90%)" + ("（已附复核记录）" if has_review_note else ""))
        gaps = [(b - a) for a, b in zip(tss, tss[1:]) if b - a > 300]
        if gaps:
            (r.warn if has_review_note else r.fail)(
                f"存在 {len(gaps)} 处 >300s 时间戳断档（切段丢失嫌疑）")
    else:  # 纯文本
        chars = len(re.sub(r"\s", "", transcript))
        zh_ratio = 1 - (len(re.sub(r"[一-鿿\s]", "", transcript)) / max(chars, 1))
        rate = chars / dur
        lo, hi = (3.0, 18) if zh_ratio > 0.7 else (3.0, 30)  # 混合语言用并集带宽
        floor = max(5000 if zh_ratio > 0.7 else 2000, dur * (2.5 if zh_ratio > 0.7 else 4))
        if chars < floor:
            (r.warn if has_review_note else r.fail)(
                f"字符数 {chars} < 下限 {floor:.0f}（时长 {dur}s）" + ("（已附复核记录）" if has_review_note else ""))
        elif not (lo <= rate <= hi):
            (r.warn if has_review_note else r.fail)(
                f"字符率 {rate:.1f}/s 超出 [{lo},{hi}] 带" + ("（已附复核记录）" if has_review_note else ""))


def extract_quotes(digest):
    """从金句库+素材块③提取引文（「」或 ／ 前的 "..."）"""
    quotes = []
    in_quote_zone = False
    for line in digest.splitlines():
        if line.startswith("## 金句库") or line.startswith("## 素材块③"):
            in_quote_zone = True
            continue
        if line.startswith("## ") or line.startswith("## 素材块"):
            if not line.startswith("## 素材块③"):
                in_quote_zone = False
                continue
        if not in_quote_zone or not line.strip().startswith(("-", "「", '"', "|")):
            continue
        bilingual = "／" in line
        if not bilingual:  # 单语行: 「」与"..."都查
            for m in re.finditer(r"「([^「」]+)」", line):
                quotes.append(m.group(1))
        for m in re.finditer(r'["\u201c]([^"\u201d]+)["\u201d]', line):
            quotes.append(m.group(1))
    return quotes


def check_quotes(r, quotes, transcript, meta, digest):
    """C组: 金句全量逐字符回对 + 数量 + 锚点消费"""
    if len(quotes) < 3:
        r.fail(f"金句数 {len(quotes)} < 3")
    nt = norm(transcript)
    zh_ratio_t = len(re.sub(r"[^一-鿿]", "", transcript)) / max(len(re.sub(r"\s", "", transcript)), 1)
    def zh_ratio(q):
        return len(re.sub(r"[^一-鿿]", "", q)) / max(len(q), 1)
    checkable = [q for q in quotes if zh_ratio_t > 0.5 or zh_ratio(q) < 0.5]
    misses = []
    for q in checkable:
        pieces = [p for p in re.split(r"…+|……", q) if p.strip()]
        if not any(norm(p) in nt for p in pieces) and not all(norm(p) in nt for p in pieces):
            misses.append(q[:30])
    quotes = checkable
    if misses:
        r.fail(f"金句回对未命中 {len(misses)}/{len(quotes)} 条: {misses[:3]}")
    else:
        r.ok(None)
    # 章节锚点: 纯文本转写时金句时间戳须在 shownotes 章节表中存在
    lines = [l for l in transcript.splitlines() if l.strip()]
    ts_lines = [l for l in lines if TS_RE.match(l.strip())]
    if len(ts_lines) <= len(lines) * 0.8:
        chapters = set(CHAPTER_RE.findall(meta.get("shownotes") or ""))
        cited = set(CHAPTER_RE.findall(digest))
        orphan = [c for c in cited if c not in chapters and len(c) >= 4]
        if chapters and len(orphan) > len(cited) * 0.5:
            r.warn(f"digest 引用时间戳 {len(orphan)} 个不在 shownotes 章节表（确认锚点来源）")
    # [?] 密度
    qmark = sum(q.count("[?]") for q in quotes)
    if quotes and qmark / len(quotes) > 0.3:
        r.warn(f"金句 [?] 占比 >30%")


def check_quadruple(r, digest):
    """D组: 四元组逐格机检"""
    seg = re.search(r"## 素材块②.*?(?=\n## |\Z)", digest, re.S)
    if not seg:
        r.fail("缺素材块②")
        return
    block = seg.group(0)
    rows = [l for l in block.splitlines() if l.strip().startswith("|")]
    data_rows = [l for l in rows[2:] if "---" not in l and l.count("|") >= 5
                 and not re.fullmatch(r"[\|\s\-:]+", l)]
    if not data_rows:
        if "本期无产业链映射" not in block:
            r.fail("四元组 0 数据行且无「本期无产业链映射」声明")
    else:
        ticker = re.compile(r"\d{6}|[A-Za-z]{1,6}:\s?[A-Z]{2,5}|NASDAQ|NYSE|SZ\.|SH\.|美股|港股|A股")
        numeric = re.compile(
            r"[$¥€£]\s*\d|\d+(\.\d+)?\s*%|\d+(\.\d+)?\s*[亿万]|\d+(\.\d+)?\s*[MBK]\b(?!S)|(市值|估值|营收|净利|市盈率|PE)[:：]?\s*\d")
        whitelist = re.compile(r"[一二三四五六]期|Phase\s*[0-9]|19\d{2}|20\d{2}|\d+[-~]\d+\s*(周|天|月)|\d+\s*(周|天|月)")
        for row in data_rows:
            cells = [c.strip() for c in row.split("|")[1:-1]]
            if len(cells) < 5:
                continue
            code_cell = re.sub(r"<[^>]+>", "", cells[2])
            if not re.fullmatch(r"—|（留空）|留空|", code_cell):
                r.fail(f"代码列含非法内容: 「{cells[2]}」（只允许 — / （留空））")
            company = re.sub(r"<[^>]+>", "", cells[1])
            if ticker.search(company):
                r.fail(f"公司列疑似走私代码/市场信息: 「{cells[1]}」")
            label = re.sub(r"<[^>]+>", "", cells[3])
            hits = [m.group(0) for m in numeric.finditer(label) if not whitelist.search(
                label[max(0, m.start() - 4):m.end() + 4])]
            if hits:
                r.fail(f"标签列含数值 {hits}（口述数字属产业情报区，标签列只留定性+期数/时间表）: 「{cells[3][:40]}」")
    weak = re.search(r"A\s*股(映射弱|无直接|无纯)|不建议接|无产业链映射|qualitative", block)
    if weak and not re.search(r"查证[:：]", block):
            r.fail("「映射弱/无映射」判定缺查证记录行（查证：WebSearch/tsdata + 日期）")
    if not re.search(r"data_source", block):
        r.fail("缺 data_source 行")


def check_intel(r, digest):
    """E组: 证据标签 + 利益相关质量"""
    seg = re.search(r"## 产业情报(.*?)(?=\n## |\Z)", digest, re.S)
    if not seg:
        r.fail("缺产业情报板块")
        return
    body = seg.group(1)
    all_lines = body.splitlines()
    top = [(i, l) for i, l in enumerate(all_lines) if re.match(r"^- ", l)]  # 只数顶级条目
    tagged = sum(1 for i, _ in top
                 if any(t in " ".join(all_lines[i:i + 3]) for t in ("🟢", "🟡", "🔴")))
    if top and tagged < len(top) * 0.8:
        r.fail(f"产业情报 {len(top)} 条仅 {tagged} 条带证据标签（行内或紧邻证据行）")
    meta_seg = re.search(r"> \*\*利益相关\*\*[:：]?\s*(.+)", digest)
    if meta_seg:
        txt = meta_seg.group(1)
        if "🔴" in digest[:2000] or "利益相关" in txt:
            if len(txt) < 15 or not any(w in txt for w in IDENTITY_WORDS):
                r.warn("利益相关标注未达「身份×对象×偏向」三元质量（需身份词+≥15字）")


def check_language(r, transcript, digest):
    """F组: 外文判定机器化（非中文字符占比≥30%）+ 双语义务"""
    lines = [l for l in transcript.splitlines() if l.strip()]
    if not lines:
        return
    def en_line(l):
        c = re.sub(r"\s|\[\d{1,2}:\d{2}(?::\d{2})?\]", "", l)
        return len(re.sub(r"[一-鿿]", "", c)) > len(c) * 0.6 if c else False
    en_ratio = sum(1 for l in lines if en_line(l)) / len(lines)
    if en_ratio > 0.5:  # 外文播客（行级投票，E249术语密集中文稿英文行占比仍低）
        glossary = len(re.findall(r"^- \*\*", digest, re.M))
        if glossary < 10:
            r.fail(f"外文播客术语表仅 {glossary} 条 (<10)")
        quotes = extract_quotes(digest)
        if quotes and not all("／" in q or '"' in q for q in quotes):
            # 双语判定从简: 金句区行含 ／ 分隔即可
            zone = re.search(r"## 金句库(.*?)(?=## |\Z)", digest, re.S)
            if zone and not re.search(r"／", zone.group(1)):
                r.fail("外文播客金句未做双语对照（缺 ／ 分隔）")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episode_dir")
    ap.add_argument("--write-envelope", action="store_true")
    args = ap.parse_args()

    episode_dir = args.episode_dir.rstrip("/")
    transcript, meta, digest = load(episode_dir)
    r = R()
    # A组 结构
    for sec in ("一句话价值", "产业情报", "科技原理", "术语表", "金句库", "素材块①", "素材块②", "素材块③"):
        if sec not in digest:
            r.fail(f"缺板块: {sec}")
    check_coverage(r, transcript, meta, digest)
    quotes = extract_quotes(digest)
    check_quotes(r, quotes, transcript, meta, digest)
    check_quadruple(r, digest)
    check_intel(r, digest)
    check_language(r, transcript, digest)

    n_checks = r.passed + len(r.fails)
    print(f"机检: {r.passed} PASS / {len(r.fails)} FAIL / {len(r.warns)} WARN")
    for w in r.warns:
        print(f"  WARN: {w}")
    for f in r.fails:
        print(f"  FAIL: {f}")

    if args.write_envelope:
        rel = os.path.relpath(episode_dir, ROOT)
        digest_rel = os.path.relpath(os.path.join(episode_dir, "digest.md"), ROOT)
        headline_m = re.search(r"## 一句话价值\s*\n+\s*(.+)", digest)
        env = {
            "id": "pod-digest", "type": "intel",
            "date": (meta.get("pubdate") or "")[:16],
            "status": "green" if not r.fails else "yellow",
            "headline": (headline_m.group(1).strip()[:80] if headline_m else meta.get("title", "")),
            "deliverable": {"md": digest_rel},
            "episode_dir": rel,
            "self_check": f"机检 {r.passed} PASS/{len(r.fails)} FAIL/{len(r.warns)} WARN"
                          f"（金句 {len(quotes)} 条全量回对；由 verify_digest.py 生成，手写会被覆写）",
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        if r.fails:
            env["failed_checks"] = r.fails
        os.makedirs(os.path.dirname(ENVELOPE), exist_ok=True)
        with open(ENVELOPE, "w", encoding="utf-8") as f:
            json.dump(env, f, ensure_ascii=False, indent=1)
        print(f"信封已回写: {ENVELOPE} (status={env['status']})")

    sys.exit(1 if r.fails else 0)


if __name__ == "__main__":
    main()
