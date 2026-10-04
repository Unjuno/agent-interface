import unittest, time, io, hashlib, json, pathlib
from PIL import Image
from runtime.guarded_win32_v1.worker_effect import PixelEffect

class SparseEffectCases(unittest.TestCase):

    def test_full_hd_exact_corner_conditions_fit_bounded_request(self):
        image = Image.new('RGB', (1920, 1080), (0, 0, 255))
        png = io.BytesIO()
        image.save(png, format='PNG')
        row = {'session_scope': 'owned-full-hd-fixture', 'sequence': 3, 'binding_revision': 0, 'native': {'artifact': {'sha256': hashlib.sha256(png.getvalue()).hexdigest()}}}
        outcomes = []
        for expected in ([0, 0, 255], [255, 0, 0]):
            effect = PixelEffect([{'point': [1919, 1079], 'rgb': expected}], time.monotonic_ns() + 3000000000)
            result = effect({}, {}, row, image)
            self.assertIs(result, expected == [0, 0, 255])
            self.assertLess(effect.receipt['payload_bytes'], 2048)
            self.assertEqual(effect.receipt['exit'], 0)
            outcomes.append({'expected': expected, 'result': result, 'payload_bytes': effect.receipt['payload_bytes'], 'worker_pid': effect.receipt['pid'], 'exit': effect.receipt['exit']})
        pathlib.Path('sparse-raw.json').write_text(json.dumps({'image_size': [1920, 1080], 'raw_rgb_bytes': 1920 * 1080 * 3, 'outcomes': outcomes}, indent=2), encoding='utf-8')
if __name__ == '__main__':
    unittest.main()
