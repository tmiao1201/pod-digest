import importlib.util
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

from PIL import Image

SPEC = importlib.util.find_spec('scripts.make_video')
VIDEO = None
if SPEC:
    VIDEO = importlib.util.module_from_spec(SPEC)
    SPEC.loader.exec_module(VIDEO)


class VideoTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(VIDEO, 'Reusable narrated-video module is not implemented yet')
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def plan(self, **changes):
        Image.new('RGB', (64, 96), '#FAF8F1').save(self.root / 'card.png')
        data = {'label': '测试播客 E001', 'scenes': [
            {'id': 1, 'image': 'card.png', 'text': '总生存仍待随访。'}]}
        data.update(changes)
        path = self.root / 'narration.json'
        path.write_text(json.dumps(data, ensure_ascii=False))
        return path

    def test_image_paths_are_relative_to_plan_not_shell_directory(self):
        plan = VIDEO.load_plan(self.plan())
        self.assertEqual(Path(plan['scenes'][0]['image']), (self.root / 'card.png').resolve())

    def test_empty_scenes_rejected_before_any_speech_request(self):
        with self.assertRaisesRegex(ValueError, 'scenes'):
            VIDEO.load_plan(self.plan(scenes=[]))

    def test_duplicate_scene_ids_rejected(self):
        scene = {'id': 1, 'image': 'card.png', 'text': '测试。'}
        with self.assertRaisesRegex(ValueError, 'id'):
            VIDEO.load_plan(self.plan(scenes=[scene, scene]))

    def test_transparent_card_requires_visual_correction(self):
        path = self.plan()
        Image.new('RGBA', (64, 96), (255, 255, 255, 0)).save(self.root / 'card.png')
        with self.assertRaisesRegex(ValueError, '透明|opaque'):
            VIDEO.load_plan(path)

    def test_timing_text_mismatch_cannot_hide_changed_medical_claim(self):
        words = [{'text': '已证实', 'offset': 0, 'duration': 10000000}]
        with self.assertRaisesRegex(ValueError, '匹配|match'):
            VIDEO.make_cues('仍待随访。', words, 2.0)

    def test_long_unpunctuated_text_has_readable_nonoverlapping_cues(self):
        text = '这是用于验证字幕可以根据真实词语时间拆分而不是按字数猜测声音位置的一段长文字'
        words = [{'text': c, 'offset': i * 2000000, 'duration': 1800000}
                 for i, c in enumerate(text)]
        cues = VIDEO.make_cues(text, words, len(text) * 0.2 + 0.5, max_chars=12)
        self.assertEqual(''.join(c['text'] for c in cues), text)
        self.assertTrue(all(len(c['text']) <= 12 for c in cues))
        self.assertTrue(all(a['end'] <= b['start'] for a, b in zip(cues, cues[1:])))
        self.assertGreater(cues[-1]['start'], 3.0)

    def test_timing_beyond_audio_is_rejected(self):
        with self.assertRaisesRegex(ValueError, '时间|duration'):
            VIDEO.make_cues('测试', [{'text': '测试', 'offset': 30000000, 'duration': 10000000}], 1.0)

    def test_scene_duration_follows_speech_and_preserves_transition_silence(self):
        scenes, total = VIDEO.make_timeline([1.1, 3.4, 0.9])
        self.assertGreater(scenes[1]['duration'], scenes[0]['duration'])
        self.assertAlmostEqual(total * 30, round(total * 30))
        for i, duration in enumerate([1.1, 3.4, 0.9]):
            self.assertLessEqual(scenes[i]['audio_start'] + duration,
                                 scenes[i]['start'] + scenes[i]['duration'])
        for a, b in zip(scenes, scenes[1:]):
            self.assertGreater(b['audio_start'], a['audio_start'] + a['audio_duration'])

    def test_existing_outputs_are_never_overwritten(self):
        out = self.root / 'result'
        out.mkdir()
        marker = out / 'keep.txt'
        marker.write_text('original')
        with self.assertRaises(FileExistsError):
            VIDEO.reserve_output(out)
        self.assertEqual(marker.read_text(), 'original')

    def test_reuse_rejects_audio_from_a_different_narration(self):
        plan = VIDEO.load_plan(self.plan())
        cache = self.root / 'old-run'
        cache.mkdir()
        (cache / 'narration.json').write_text(json.dumps({
            'voice': plan['voice'], 'rate': plan['rate'],
            'scenes': [{'id': 1, 'text': '总生存获益已经证实。'}]}))
        with self.assertRaisesRegex(ValueError, '旁白|narration'):
            VIDEO.validate_reuse(plan, cache)

    def test_provider_failure_keeps_error_record_without_claiming_video_success(self):
        out = self.root / 'failed-run'
        argv = ['make_video.py', str(self.plan()), '--out', str(out)]
        # Isolate external provider, font and executable availability; keep real CLI/file behavior.
        with patch.object(sys, 'argv', argv), patch.dict(sys.modules, {'edge_tts': types.ModuleType('edge_tts')}), \
             patch.object(VIDEO, 'find_font', return_value='cjk-font.ttf'), \
             patch.object(VIDEO.shutil, 'which', return_value='/available/ffmpeg'), \
             patch.object(VIDEO, 'command', return_value='zoompan xfade overlay loudnorm libx264'), \
             patch.object(VIDEO, 'synthesize', new=AsyncMock(side_effect=Exception('speech provider unavailable'))), \
             patch.object(sys, 'stderr', new_callable=io.StringIO):
            try:
                status = VIDEO.main()
            except Exception as exc:
                self.fail(f'CLI leaked provider error instead of recording failure: {exc}')
        self.assertEqual(status, 1)
        self.assertIn('speech provider unavailable', json.loads((out / 'error.json').read_text())['error'])
        self.assertFalse((out / 'video.mp4').exists())


if __name__ == '__main__':
    unittest.main()
