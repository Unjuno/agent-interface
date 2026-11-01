"""Pixel identity, old-source grounding and bounded decoded ownership."""
import gc
import hashlib
from pathlib import Path
import tempfile
import unittest
import weakref
from unittest.mock import patch

from PIL import Image
from runtime.guarded_x11_v1.history import ObservationHistory
from runtime.guarded_x11_v1.handles import TargetHandleStore


class HistoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def row(self, sequence):
        image = Image.new('RGB', (100, 80), 'white')
        for i in range(20):
            image.putpixel((20+i, 20+i%7), (i*10, sequence%256, 100))
        path = self.root/f'{sequence}.png'
        image.save(path)
        raw = hashlib.sha256(image.tobytes()).hexdigest()
        observation = {'sequence':sequence, 'capture_ns':1000,
            'pointer_binding':{'focus':10,'surface':20,'geometry':[0,0,100,80]},
            'native':{'width':100,'height':80,'sha256':raw,
                'artifact':{'path':str(path), 'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                            'source_raw_sha256':raw}}}
        return observation, image

    def test_evicted_image_collects_and_reloads_exact_pixels_for_old_mint(self):
        history = ObservationHistory()
        original, image = self.row(1)
        expected = image.tobytes()
        old = weakref.ref(image)
        history[1] = original, image
        del image
        for n in range(2, 30):
            history[n] = self.row(n)
        gc.collect()
        self.assertIsNone(old())
        self.assertEqual(len(history), 29)
        observation, reloaded = history[1]
        self.assertIs(observation, original)
        self.assertEqual(reloaded.tobytes(), expected)
        store = TargetHandleStore('history-test')
        store.mint('field', 'window_content', [20,20,24,16], observation, reloaded, 1100)
        result = store.resolve_point('field', [3,3], observation, reloaded, 1200,
                                     session_scope='history-test')
        self.assertEqual(result['point'], [23,23])

    def test_recent_access_uses_cache_and_old_access_does_not_recapture(self):
        history = ObservationHistory()
        for n in range(1, 4): history[n] = self.row(n)
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('unexpected disk access')):
            self.assertEqual(history[3][0]['sequence'], 3)
            self.assertEqual(history[2][0]['sequence'], 2)
        self.assertEqual(history[1][0]['sequence'], 1)

    def test_corruption_and_missing_old_artifact_refuse_without_fallback(self):
        for missing in (False, True):
            with self.subTest(missing=missing):
                history = ObservationHistory(1)
                history[1] = self.row(1)
                history[2] = self.row(2)
                path = self.root/'1.png'
                if missing: path.unlink()
                else: path.write_bytes((self.root/'2.png').read_bytes())
                with self.assertRaises(FileNotFoundError if missing else ValueError):
                    history[1]
                self.assertEqual(history[2][0]['sequence'], 2)

    def test_reload_identity_is_pinned_and_clear_never_loads_artifacts(self):
        history = ObservationHistory(1)
        history[1] = self.row(1)
        observation, image = history[1]
        expected = image.tobytes()
        history[2] = self.row(2)
        observation['native']['artifact']['path'] = str(self.root/'2.png')
        self.assertEqual(history[1][1].tobytes(), expected)
        with patch.object(Path, 'read_bytes', side_effect=AssertionError('unexpected read')):
            del history[1]
            history.clear()
        self.assertEqual(len(history), 0)
        with self.assertRaises(KeyError): history[2]

    def test_validation_and_caller_held_images(self):
        for capacity in (0, -1, True, 1.0):
            with self.assertRaises(ValueError): ObservationHistory(capacity)
        history = ObservationHistory(1)
        observation, image = self.row(1)
        history[1] = observation, image
        history[2] = self.row(2)
        self.assertEqual(image.getpixel((0,0)), (255,255,255))
        observation['native']['artifact']['source_raw_sha256'] = 'wrong'
        with self.assertRaises(ValueError): history[3] = observation, image
        self.assertNotIn(3, history)


if __name__ == '__main__': unittest.main()
