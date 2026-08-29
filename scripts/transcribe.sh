#!/usr/bin/env bash
# transcribe.sh — 转写调度器：音频文件 → 带时间戳逐字稿
# 用法: transcribe.sh <audio_file> <out_txt> [--engine auto|agent-reach|groq-direct] [--lang auto|zh|en]
# 引擎说明见 ../references/acquisition.md
set -uo pipefail

AUDIO="${1:?用法: transcribe.sh <audio> <out_txt> [--engine ...] [--lang ...]}"
OUT="${2:?缺少输出路径}"
shift 2

ENGINE="auto"
LANG_="auto"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --engine) ENGINE="$2"; shift 2 ;;
    --lang)   LANG_="$2"; shift 2 ;;
    *) echo "未知参数: $1" >&2; exit 1 ;;
  esac
done
DIR="$(cd "$(dirname "$0")" && pwd)"

if [[ "$ENGINE" == "auto" ]]; then
  # 有 agent-reach 且其后端 ok → 用它（key 委托 agent-reach 管）；否则 GROQ_API_KEY 直连
  if command -v agent-reach >/dev/null 2>&1 \
     && agent-reach doctor --json 2>/dev/null | python3 -c "
import json, sys
try:
    d = json.load(sys.stdin)
    y = d.get('platforms', d).get('youtube', {})   # 顶层可能是 {platforms:{...}} 或直接平铺
    sys.exit(0 if y.get('status') == 'ok' else 1)
except Exception:
    sys.exit(1)"; then
    ENGINE="agent-reach"
  elif [[ -n "${GROQ_API_KEY:-}" ]] || grep -qE "^groq(_api)?_key:" ~/.agent-reach/config.yaml 2>/dev/null; then
    ENGINE="groq-direct"
  else
    echo "无可用转写引擎：既没有可用的 agent-reach 后端，也未设置 GROQ_API_KEY。" >&2
    echo "解决: ①免费注册 https://console.groq.com/keys 后 export GROQ_API_KEY=... ；或 ② agent-reach configure groq-key <key> && agent-reach install --env=auto" >&2
    exit 1
  fi
fi

# groq-direct 的 key 来源: 环境变量优先，其次从 agent-reach 的 config.yaml 借用（用户已配过就不必再export）
if [[ "$ENGINE" == "groq-direct" && -z "${GROQ_API_KEY:-}" ]]; then
  export GROQ_API_KEY=$(awk '/^groq(_api)?_key:/ {print $2; exit}' ~/.agent-reach/config.yaml 2>/dev/null)
fi

case "$ENGINE" in
  groq-direct)
    exec python3 "$DIR/transcribe_groq.py" "$AUDIO" "$OUT" --lang "$LANG_"
    ;;
  agent-reach)
    # agent-reach transcribe 语法: transcribe <source> -o <out> [--provider auto|groq|openai]（无 --lang 参数）
    if agent-reach transcribe "$AUDIO" -o "$OUT" 2>/tmp/pod-digest/agent_reach_err.log; then
      echo "✅ 转写完成（agent-reach）→ $OUT"
    else
      echo "agent-reach 转写失败（$(tail -1 /tmp/pod-digest/agent_reach_err.log)），降级 groq-direct" >&2
      exec python3 "$DIR/transcribe_groq.py" "$AUDIO" "$OUT" --lang "$LANG_"
    fi
    ;;
  *)
    echo "未知引擎: $ENGINE（可选 auto | agent-reach | groq-direct）" >&2; exit 1 ;;
esac
