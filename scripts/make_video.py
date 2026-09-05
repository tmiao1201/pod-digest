#!/usr/bin/env python3
"""Narration JSON + opaque cards -> voiced portrait MP4, SRT and QA evidence.

Optional dependencies: requirements-video.txt; system FFmpeg and a CJK font.
See references/narrated-video.md. Imports do not contact the speech service.
"""
import argparse
import asyncio
import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import wave
from pathlib import Path

FPS, SAMPLE_RATE = 30, 48000
LEAD, TAIL, TRANSITION = 0.5, 0.5, 0.4


def normalized(text):
    return ''.join(c.lower() for c in text if c.isalnum())


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def load_plan(path):
    from PIL import Image
    path = Path(path).resolve()
    plan = json.loads(path.read_text(encoding='utf-8'))
    if not isinstance(plan, dict) or not isinstance(plan.get('scenes'), list) or not plan['scenes']:
        raise ValueError('scenes 必须是非空数组')
    plan.setdefault('voice', 'zh-CN-XiaoxiaoNeural')
    plan.setdefault('rate', '+3%')
    plan.setdefault('label', plan.get('source_episode', '播客精编'))
    if not isinstance(plan['label'], str) or not plan['label'].strip():
        raise ValueError('label 必须是非空文字')
    ids = set()
    for index, scene in enumerate(plan['scenes'], 1):
        if not isinstance(scene, dict):
            raise ValueError('scenes 中每项必须是对象')
        scene.setdefault('id', index)
        sid = scene['id']
        if type(sid) is not int or sid < 1 or sid in ids:
            raise ValueError('scene id 必须是互不重复的正整数')
        ids.add(sid)
        if not isinstance(scene.get('text'), str) or not normalized(scene['text']):
            raise ValueError(f'scene {sid} 缺少有效旁白 text')
        if not isinstance(scene.get('image'), str) or not scene['image']:
            raise ValueError(f'scene {sid} 缺少 image')
        image = (path.parent / scene['image']).resolve()
        with Image.open(image) as im:
            im.load()
            if im.convert('RGBA').getchannel('A').getextrema()[0] != 255:
                raise ValueError(f'图卡含透明像素，请先修正为 opaque 图片：{image}')
        scene['image'] = str(image)
    return plan


def make_timeline(durations, fps=FPS, transition=TRANSITION, lead=LEAD, tail=TAIL):
    if not durations or any(not math.isfinite(d) or d <= 0 for d in durations):
        raise ValueError('音频 duration 必须是正数')
    if transition < 0 or lead < transition or tail < 0:
        raise ValueError('转场不得越过下一段配音的开始时间')
    scenes, cursor = [], 0
    overlap = round(transition * fps)
    for duration in durations:
        frames = math.ceil((duration + lead + tail) * fps)
        scenes.append({'start': cursor / fps, 'duration': frames / fps, 'frames': frames,
                       'audio_start': cursor / fps + lead, 'audio_duration': duration})
        cursor += frames - overlap
    return scenes, (cursor + overlap) / fps


def make_cues(text, words, audio_duration, scene_start=0, lead=LEAD, fps=FPS, max_chars=16):
    if not words or normalized(''.join(w['text'] for w in words)) != normalized(text):
        raise ValueError('配音时间数据与旁白不匹配 (text mismatch)')
    positions = [i for i, c in enumerate(text) if c.isalnum()]
    cues, buffer, pos, raw_pos, last_start = [], '', 0, 0, -1.0
    begin = end = 0.0

    def flush():
        nonlocal buffer
        if buffer.strip():
            cues.append({'text': buffer.strip(), 'start': scene_start + lead + begin,
                         'end': scene_start + lead + end + 0.08})
        buffer = ''

    for word in words:
        start = word['offset'] / 1e7
        finish = (word['offset'] + word['duration']) / 1e7
        if not all(math.isfinite(t) for t in (start, finish)) or start < last_start or start < 0 or finish <= start or finish > audio_duration + 0.05:
            raise ValueError('配音词语时间超出音频 duration 或顺序异常')
        last_start = start
        count = len(normalized(word['text']))
        if not count:
            continue
        pos += count
        next_raw = positions[pos] if pos < len(positions) else len(text)
        fragment = text[raw_pos:next_raw]
        raw_pos = next_raw
        if buffer and len(buffer.strip()) + len(fragment.strip()) > max_chars:
            flush()
        if not buffer:
            begin = start
        buffer += fragment
        end = finish
        if re.search(r'[，。！？；：,!?;:]\s*$', fragment):
            flush()
    flush()
    for i, cue in enumerate(cues):
        limit = cues[i + 1]['start'] if i + 1 < len(cues) else scene_start + lead + audio_duration
        cue['start'] = round(cue['start'] * fps) / fps
        cue['end'] = round(min(cue['end'], limit) * fps) / fps
        if cue['end'] <= cue['start']:
            raise ValueError('字幕时间短于一帧，需调整配音语速')
    return cues


def reserve_output(path):
    path = Path(path).resolve()
    path.mkdir(parents=True, exist_ok=False)
    return path


def validate_reuse(plan, folder):
    folder = Path(folder).resolve()
    old = json.loads((folder / 'narration.json').read_text(encoding='utf-8'))
    pairs = lambda p: [(s['id'], s['text']) for s in p['scenes']]
    if pairs(old) != pairs(plan) or old.get('voice') != plan['voice'] or old.get('rate') != plan['rate']:
        raise ValueError('复用音频的旁白、音色或语速与 narration 不一致')
    for s in plan['scenes']:
        for suffix in ('mp3', 'jsonl'):
            file = folder / f"voice-{s['id']:02}.{suffix}"
            if not file.is_file() or not file.stat().st_size:
                raise ValueError(f'缺少可复用音频或词语时间数据：{file}')
    return folder


def command(args, log=None):
    if log:
        with Path(log).open('w', encoding='utf-8') as stream:
            result = subprocess.run(args, stdout=stream, stderr=subprocess.STDOUT)
        if result.returncode:
            raise RuntimeError(f'命令失败，见 {log}\n' + Path(log).read_text(encoding='utf-8')[-3000:])
        return ''
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError(result.stderr[-3000:])
    return result.stdout


def find_font(requested=None):
    from PIL import ImageFont
    candidates = [requested] if requested else [
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/PingFang.ttc',
        '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
        '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
        'C:/Windows/Fonts/msyh.ttc',
    ]
    for name in candidates:
        if name and Path(name).is_file():
            ImageFont.truetype(str(name), 32)
            return str(Path(name).resolve())
    raise ValueError('未找到中文字体；请用 --font 指定可读取的中文 TTF/TTC 字体')


async def synthesize(plan, out):
    import edge_tts
    for scene in plan['scenes']:
        sid = scene['id']
        speech = edge_tts.Communicate(scene['text'], voice=plan['voice'], rate=plan['rate'], boundary='WordBoundary')
        await speech.save(str(out / f'voice-{sid:02}.mp3'), str(out / f'voice-{sid:02}.jsonl'))
        print(f'配音完成 {sid}', flush=True)


def prepare_audio(plan, out):
    durations, samples = [], []
    for scene in plan['scenes']:
        sid = scene['id']
        wav = out / f'voice-{sid:02}.wav'
        command(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', str(out / f'voice-{sid:02}.mp3'),
                 '-ar', str(SAMPLE_RATE), '-ac', '1', '-c:a', 'pcm_s16le', str(wav)])
        with wave.open(str(wav), 'rb') as stream:
            durations.append(stream.getnframes() / SAMPLE_RATE)
            samples.append(stream.readframes(stream.getnframes()))
    timeline, total = make_timeline(durations)
    pcm = bytearray(round(total * SAMPLE_RATE) * 2)
    cues = []
    for scene, timing, data in zip(plan['scenes'], timeline, samples):
        sid = scene['id']
        words = [json.loads(line) for line in (out / f'voice-{sid:02}.jsonl').read_text().splitlines()]
        for cue in make_cues(scene['text'], words, timing['audio_duration'], timing['start']):
            cues.append({**cue, 'scene': sid})
        start = round(timing['audio_start'] * SAMPLE_RATE) * 2
        pcm[start:start + len(data)] = data
    with wave.open(str(out / 'narration.wav'), 'wb') as stream:
        stream.setnchannels(1)
        stream.setsampwidth(2)
        stream.setframerate(SAMPLE_RATE)
        stream.writeframes(pcm)
    return timeline, cues, total


def srt_stamp(seconds):
    ms = round(seconds * 1000)
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def prepare_captions(plan, cues, total, font_path, out):
    from PIL import Image, ImageDraw, ImageFont
    directory = out / 'caption-overlays'
    directory.mkdir()
    base = Image.new('RGBA', (1080, 1920), (0, 0, 0, 0))
    draw = ImageDraw.Draw(base)
    header_font = ImageFont.truetype(font_path, 29)
    if draw.textlength(plan['label'], font=header_font) > 590:
        raise ValueError('label 太长，请缩短节目与集数标签')
    draw.text((66, 77), plan['label'], font=header_font, fill='#173C4B')
    label = 'AI 配音 · 节目精编'
    label_font = ImageFont.truetype(font_path, 27)
    draw.text((1014 - draw.textlength(label, font=label_font), 79), label, font=label_font, fill='#657A7F')
    draw.line((66, 127, 1014, 127), fill='#D5DCD7', width=2)
    base.save(directory / 'empty.png')
    concat = ['ffconcat version 1.0']
    cursor = 0

    def emit(name, frames):
        if frames > 0:
            concat.extend([f"file '{name}'", 'option framerate 30', f'duration {frames / FPS:.9f}'])

    for i, cue in enumerate(cues):
        start, end = round(cue['start'] * FPS), round(cue['end'] * FPS)
        emit('empty.png', start - cursor)
        image = base.copy()
        draw = ImageDraw.Draw(image)
        size = 52
        font = ImageFont.truetype(font_path, size)
        while draw.textlength(cue['text'], font=font) > 946 and size > 32:
            size -= 2
            font = ImageFont.truetype(font_path, size)
        if draw.textlength(cue['text'], font=font) > 946:
            raise ValueError('单个字幕词组太长，请在旁白中分句：' + cue['text'])
        left, top, right, bottom = draw.textbbox((0, 0), cue['text'], font=font)
        width, height = right - left, bottom - top
        draw.rounded_rectangle((510 - width / 2, 1744, 570 + width / 2, 1848), radius=20, fill=(23, 60, 75, 245))
        draw.text((540 - width / 2 - left, 1796 - height / 2 - top), cue['text'], font=font, fill='white')
        name = f'caption-{i+1:03}.png'
        image.save(directory / name)
        emit(name, end - start)
        cursor = end
    emit('empty.png', round(total * FPS) - cursor)
    concat.extend(["file 'empty.png'", 'option framerate 30'])
    (directory / 'captions.ffconcat').write_text('\n'.join(concat) + '\n', encoding='utf-8')
    (out / 'subtitles.srt').write_text('\n\n'.join(
        f"{i+1}\n{srt_stamp(c['start'])} --> {srt_stamp(c['end'])}\n{c['text']}"
        for i, c in enumerate(cues)) + '\n', encoding='utf-8')


def render(plan, timeline, total, out):
    inputs, filters = [], []
    count = len(plan['scenes'])
    for i, (scene, timing) in enumerate(zip(plan['scenes'], timeline)):
        inputs.extend(['-i', scene['image']])
        end = timing['frames'] - 1
        movement = f'0.022*(1-cos(PI*on/{end}))/2'
        zoom = '1+' + movement if i % 2 == 0 else '1.022-' + movement
        filters.append(f"[{i}:v]scale=2000:2960:force_original_aspect_ratio=decrease:flags=lanczos,"
                       'pad=2160:3840:(ow-iw)/2:(oh-ih)/2:color=0xFAF8F1,'
                       f"zoompan=z='{zoom}':x='iw/2-iw/zoom/2':y='ih/2-ih/zoom/2':d={timing['frames']}:s=1080x1920:fps=30,"
                       f'setsar=1,settb=AVTB,setpts=PTS-STARTPTS[v{i}]')
    last = 'v0'
    for i in range(1, count):
        name = f'x{i}'
        filters.append(f'[{last}][v{i}]xfade=transition=fade:duration={TRANSITION}:offset={timeline[i]["start"]:.9f}[{name}]')
        last = name
    filters.append(f'[{count}:v]fps=30,settb=AVTB,setpts=PTS-STARTPTS,format=rgba[captions]')
    filters.append(f'[{last}][captions]overlay=0:0:format=auto:eof_action=repeat,'
                   f'fade=t=in:st=0:d=0.25:color=0xFAF8F1,fade=t=out:st={total-0.35:.9f}:d=0.35:color=0xFAF8F1,format=yuv420p[outv]')
    filters.append(f'[{count+1}:a]loudnorm=I=-16:TP=-1.5:LRA=9,aresample=48000[outa]')
    graph = ';\n'.join(filters)
    (out / 'filtergraph.txt').write_text(graph)
    output = out / 'video.mp4'
    args = ['ffmpeg', '-hide_banner', '-nostdin', '-n', '-filter_complex_threads', '2', *inputs,
            '-f', 'concat', '-safe', '0', '-i', str(out / 'caption-overlays' / 'captions.ffconcat'),
            '-i', str(out / 'narration.wav'), '-filter_complex', graph, '-map', '[outv]', '-map', '[outa]',
            '-c:v', 'libx264', '-threads', '4', '-preset', 'fast', '-crf', '19', '-pix_fmt', 'yuv420p',
            '-r', str(FPS), '-c:a', 'aac', '-b:a', '160k', '-ar', str(SAMPLE_RATE),
            '-t', str(total), '-movflags', '+faststart', str(output)]
    command(args, out / 'render.log')
    return output


def verify(output, timeline, cues, total, out):
    probe = json.loads(command(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', str(output)]))
    video = next((s for s in probe['streams'] if s['codec_type'] == 'video'), {})
    audio = next((s for s in probe['streams'] if s['codec_type'] == 'audio'), {})
    checks = {
        'h264_video': video.get('codec_name') == 'h264', 'aac_audio': audio.get('codec_name') == 'aac',
        'portrait_size': [video.get('width'), video.get('height')] == [1080, 1920],
        'fps_30': video.get('avg_frame_rate') == '30/1', 'yuv420p': video.get('pix_fmt') == 'yuv420p',
        'frame_count': int(video.get('nb_frames', -1)) == round(total * FPS),
        'duration': abs(float(probe['format']['duration']) - total) < 0.05,
        'audio_video_duration': abs(float(video.get('duration', -1)) - float(audio.get('duration', -10))) < 0.05,
    }
    command(['ffmpeg', '-hide_banner', '-nostdin', '-v', 'info', '-i', str(output),
             '-vf', 'blackdetect=d=0.1:pix_th=0.05',
             '-af', 'loudnorm=I=-16:TP=-1.5:LRA=9:print_format=json', '-f', 'null', '-'], out / 'decode.log')
    log = (out / 'decode.log').read_text()
    checks['full_decode'] = not re.search(r'Error while decoding|Invalid data found|corrupt', log, re.I)
    checks['no_black_intervals'] = 'black_start:' not in log
    meter = json.loads(log[log.rfind('{'):log.rfind('}')+1])
    checks['speech_loudness'] = -19 < float(meter['input_i']) < -13
    checks['peak_below_zero'] = float(meter['input_tp']) < 0
    samples = []
    for i, timing in enumerate(timeline):
        cue = next(c for c in cues if timing['audio_start'] <= c['start'] < timing['start'] + timing['duration'])
        second = (cue['start'] + cue['end']) / 2
        path = out / f'qa-scene-{i+1:02}.jpg'
        command(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-ss', str(second), '-i', str(output), '-frames:v', '1', str(path)])
        samples.append(path.name)
    command(['ffmpeg', '-v', 'error', '-nostdin', '-n', '-i', str(output), '-vn', '-c:a', 'copy', str(out / 'narration.m4a')])
    report = {'checks': checks, 'duration_seconds': float(probe['format']['duration']), 'bytes': output.stat().st_size,
              'sha256': hashlib.sha256(output.read_bytes()).hexdigest(), 'audio_loudness': meter,
              'visual_review': 'pending; inspect ' + ', '.join(samples),
              'auditory_review': 'not performed by this script', 'fact_review': 'must be recorded separately by the author'}
    write_json(out / 'verification.json', report)
    if not all(checks.values()):
        raise ValueError('成片验证未通过：' + ', '.join(k for k, v in checks.items() if not v))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path, help='旁白、图卡和证据的 narration.json')
    parser.add_argument('--out', type=Path, required=True, help='必须是不存在的新输出目录')
    parser.add_argument('--voice', help='覆盖音色；默认 zh-CN-XiaoxiaoNeural')
    parser.add_argument('--rate', help='覆盖语速，例如 +3%% 或 --rate=-5%%')
    parser.add_argument('--font', help='中文 TTF/TTC 字体路径')
    parser.add_argument('--reuse-audio', type=Path, help='复用同一旁白、音色、语速的旧运行音频，跳过网络配音')
    parser.add_argument('--check-only', action='store_true', help='检查输入和依赖，不联网、不写输出')
    args = parser.parse_args()
    out = None
    try:
        plan = load_plan(args.plan)
        plan['voice'] = args.voice or plan['voice']
        plan['rate'] = args.rate or plan['rate']
        if not isinstance(plan['voice'], str) or not isinstance(plan['rate'], str) or not re.fullmatch(r'[+-]\d+%', plan['rate']):
            raise ValueError('voice 应为音色名称，rate 应为带符号的百分比，例如 +3%')
        font = find_font(args.font)
        if args.out.exists():
            raise FileExistsError(f'输出目录已存在，请选择新目录：{args.out}')
        for executable in ('ffmpeg', 'ffprobe'):
            if not shutil.which(executable):
                raise ValueError(f'缺少 {executable}，请先安装 FFmpeg')
        filters = command(['ffmpeg', '-hide_banner', '-filters'])
        encoders = command(['ffmpeg', '-hide_banner', '-encoders'])
        if any(name not in filters for name in ('zoompan', 'xfade', 'overlay', 'loudnorm')) or 'libx264' not in encoders:
            raise ValueError('FFmpeg 缺少所需过滤器或 libx264 编码器')
        reuse = validate_reuse(plan, args.reuse_audio) if args.reuse_audio else None
        if not reuse:
            import edge_tts  # noqa: F401 -- verify optional dependency before creating output
        if args.check_only:
            print(json.dumps({'status': 'ready', 'scenes': len(plan['scenes']), 'font': font, 'network_used': False}, ensure_ascii=False))
            return 0
        out = reserve_output(args.out)
        write_json(out / 'narration.json', plan)
        if reuse:
            for scene in plan['scenes']:
                for ext in ('mp3', 'jsonl'):
                    name = f"voice-{scene['id']:02}.{ext}"
                    shutil.copy2(reuse / name, out / name)
        else:
            asyncio.run(synthesize(plan, out))
        timeline, cues, total = prepare_audio(plan, out)
        prepare_captions(plan, cues, total, font, out)
        write_json(out / 'video-manifest.json', {'type': 'narrated_card_video', 'voice': plan['voice'], 'rate': plan['rate'],
                   'tts': 'Microsoft Edge online TTS via edge-tts', 'reused_audio': str(reuse) if reuse else None,
                   'size': [1080, 1920], 'fps': FPS, 'duration_seconds': total,
                   'scenes': [{**s, **t} for s, t in zip(plan['scenes'], timeline)], 'cues': cues})
        (out / 'narration.md').write_text('# 配音旁白\n\n' + '\n\n'.join(s['text'] for s in plan['scenes']) + '\n', encoding='utf-8')
        print(f'开始合成 {total:.2f} 秒视频，{len(cues)} 条字幕', flush=True)
        output = render(plan, timeline, total, out)
        report = verify(output, timeline, cues, total, out)
        print(json.dumps({'output': str(output), 'duration_seconds': report['duration_seconds'],
                          'technical_checks': 'passed', 'visual_review': 'pending', 'auditory_review': 'not performed'}, ensure_ascii=False))
        return 0
    except Exception as exc:
        # Providers have their own exception classes; preserve failures at the CLI boundary.
        if out:
            write_json(out / 'error.json', {'error_type': type(exc).__name__, 'error': str(exc)})
        print(f'失败：{exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
