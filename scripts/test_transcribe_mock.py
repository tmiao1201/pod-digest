#!/usr/bin/env python3
"""test_transcribe_mock.py — 转写管道自测：不需要 Groq key，用本地 mock 服务器验证全链路

验证点: multipart 编码 / Authorization 头 / ffmpeg 切段 / 多段时间戳偏移拼接 / 输出格式
用法: python3 scripts/test_transcribe_mock.py
原理: 1) 从任意可用的音频（或合成一段正弦波）切 1600s 测试音频 → 2 段
      2) 起 localhost mock 服务器返回伪造 verbose_json
      3) 跑 transcribe_groq.py，检查产物第 2 段时间戳 ≥ 00:15:00
"""
import json
import os
import subprocess
import sys
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer

DIR = os.path.dirname(os.path.abspath(__file__))
TMP = "/tmp/pod-digest/selftest"
PORT = 18931


class MockGroq(BaseHTTPRequestHandler):
    calls = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)
        auth = self.headers.get("Authorization", "")
        ctype = self.headers.get("Content-Type", "")
        # multipart 里应包含 model / response_format / 音频字节
        ok_auth = auth == "Bearer test-key-123"
        ok_fields = b'name="model"' in body and b"whisper-large-v3" in body \
            and b'name="response_format"' in body and b"verbose_json" in body
        ok_audio = len(body) > 10000  # 有实际音频内容
        MockGroq.calls.append(ok_auth and ok_fields and ok_audio)
        # 返回伪造 segments：每段 0-10s 两条文本
        resp = {"language": "zh", "duration": 900.0, "text": "测试",
                "segments": [
                    {"id": 0, "start": 0.0, "end": 5.0, "text": "第一条测试文本"},
                    {"id": 1, "start": 300.0, "end": 305.0, "text": "第二条测试文本"},
                ]}
        data = json.dumps(resp).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *a):
        pass


def synth_audio(path, seconds):
    """无声源时合成正弦波；有 E250 真音频则从它切（更真实）"""
    real = "/tmp/pod-digest/E250_moderna.mp3"
    if os.path.exists(real):
        src = ["-i", real, "-ss", "0"]
    else:
        src = ["-f", "lavfi", "-i", f"sine=frequency=440:duration={seconds}"]
    subprocess.run(["ffmpeg", "-y", "-v", "error", *src, "-t", str(seconds),
                    "-ar", "16000", "-ac", "1", "-b:a", "48k", path], check=True)


def main():
    os.makedirs(TMP, exist_ok=True)
    audio = os.path.join(TMP, "selftest_1600s.mp3")
    out = os.path.join(TMP, "selftest_transcript.txt")
    if not os.path.exists(audio):
        print("合成/切取 1600s 测试音频...")
        synth_audio(audio, 1600)

    srv = HTTPServer(("127.0.0.1", PORT), MockGroq)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    env = {**os.environ,
           "GROQ_API_KEY": "test-key-123",
           "GROQ_API_BASE": f"http://127.0.0.1:{PORT}/openai/v1"}
    r = subprocess.run([sys.executable, os.path.join(DIR, "transcribe_groq.py"),
                        audio, out, "--lang", "zh"],
                       capture_output=True, text=True, env=env)
    print(r.stderr.strip())
    if r.returncode != 0:
        sys.exit("❌ 转写脚本退出非零")

    lines = open(out, encoding="utf-8").read().splitlines()
    print(f"产物 {len(lines)} 行:")
    for ln in lines:
        print(" ", ln)

    # 断言：2 段 × 2 条 = 4 行；第 3 行（第 2 段第 1 条）时间戳应 ≥ 00:15:00（偏移生效）
    assert len(lines) == 4, f"预期 4 行，实际 {len(lines)}"
    assert lines[0].startswith("[00:00:00]"), "第 1 行时间戳错误"
    ts2 = lines[2].split("]")[0].lstrip("[")
    assert ts2 >= "00:15:00", f"第 2 段未加偏移: {ts2}"
    assert all(MockGroq.calls), f"mock 收到的请求不合规: {MockGroq.calls}"
    print("✅ 自测通过：multipart 编码 / 认证头 / 切段 / 偏移拼接 / 输出格式 全部正确")


if __name__ == "__main__":
    main()
