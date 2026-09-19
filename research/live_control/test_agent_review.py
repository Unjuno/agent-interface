import base64
import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from agent_review import review


class ReviewTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.png = self.root / 'frame.png'
        self.pixels = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a9xkAAAAASUVORK5CYII=')
        self.png.write_bytes(self.pixels)
        self.report = self.root / 'report.json'
        self.observation = {'event': 'observation', 'sequence': 2, 'capture_ns': 12,
                            'image': str(self.png)}
        self.rows = [self.observation, {'event': 'independent_evaluation', 'success': True}]

    def write(self, **extra):
        self.report.write_text(json.dumps({'status': 'boundary', 'records': self.rows, **extra}))

    def test_image_bytes_and_full_result_share_one_response(self):
        self.write()
        original = self.report.read_bytes()
        result = review(self.report, self.root)
        self.assertEqual(base64.b64decode(result['image']['data']), self.pixels)
        self.assertEqual(result['receipt']['events'], [self.rows[-1]])
        self.assertEqual(result['receipt']['source']['sha256'], hashlib.sha256(original).hexdigest())
        self.assertEqual(self.report.read_bytes(), original)

    def test_mutated_image_preserves_result_without_rendering(self):
        self.write(image={'status': 'image', 'sequence': 2, 'capture_ns': 12,
                          'path': str(self.png), 'sha256': 'wrong'})
        result = review(self.report, self.root)
        self.assertIsNone(result['image'])
        self.assertIn('sha256', result['image_error'])
        self.assertTrue(result['receipt']['events'][0]['success'])

    def test_conflicting_latest_image_is_not_silently_selected(self):
        self.rows.append({**self.observation, 'capture_ns': 13})
        self.write()
        result = review(self.report, self.root)
        self.assertIsNone(result['image'])
        self.assertEqual(len(result['receipt']['latest_observations']), 2)

    def test_missing_latest_does_not_fall_back_to_older_image(self):
        self.rows.append({**self.observation, 'sequence': 3, 'image': str(self.root/'missing.png')})
        self.write()
        result = review(self.report, self.root)
        self.assertIsNone(result['image'])
        self.assertEqual(result['image_status'], 'needs_review')

    def test_no_observation_does_not_show_pre_action_source(self):
        self.rows = [{'event': 'rejected', 'reason': 'stale'}]
        self.write(source_image={'path': str(self.png)})
        result = review(self.report, self.root)
        self.assertIsNone(result['image'])
        self.assertEqual(result['image_status'], 'no_observation')
        self.assertEqual(result['receipt']['events'], self.rows)


if __name__ == '__main__':
    unittest.main()
