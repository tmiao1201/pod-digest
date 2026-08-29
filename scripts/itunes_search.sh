#!/usr/bin/env bash
# itunes_search.sh — 通过 iTunes Search API 查播客的 RSS feedUrl（播客界通用入口，无需 key）
# 用法: itunes_search.sh "播客名" [country]
#   country 默认 CN，无结果自动重试 US（英文播客）
# 输出: 每行 "节目名 | feedUrl"
set -uo pipefail

TERM="${1:?用法: itunes_search.sh 播客名 [country]}"
COUNTRY="${2:-CN}"

search() {
  local c="$1"
  curl -s --max-time 20 \
    "https://itunes.apple.com/search?term=$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1]))" "$TERM")&media=podcast&country=${c}&limit=8" \
  | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
except Exception:
    sys.exit(1)
for r in data.get('results', []):
    feed = r.get('feedUrl')
    if feed:
        print(f\"{r['collectionName']} | {feed}\")
"
}

# Hard Stop: CN/US 各试一次，仍无结果即停，不盲目重试
RESULT=$(search "$COUNTRY")
if [[ -z "$RESULT" && "$COUNTRY" != "US" ]]; then
  RESULT=$(search US)
fi

if [[ -z "$RESULT" ]]; then
  echo "未找到 feedUrl。可能原因: 1)节目名拼写 2)平台独家不发RSS(Spotify独家等) 3)网络。建议: 换英文名重试 / 去播客官网找 RSS 链接" >&2
  exit 1
fi
echo "$RESULT"
