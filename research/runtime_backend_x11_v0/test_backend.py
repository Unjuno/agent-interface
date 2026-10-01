import unittest
from pathlib import Path
from backend_x11 import BUTTON_MAP

class StaticTests(unittest.TestCase):
    def test_button_map(self):
        self.assertEqual(BUTTON_MAP['left'],1)
        self.assertEqual(BUTTON_MAP['right'],3)
    def test_no_native_claim_in_source(self):
        source=Path(__file__.replace('test_backend.py','backend_x11.py')).read_text(encoding='utf-8')
        self.assertNotIn('Windows backend supported',source)
        self.assertNotIn('macOS backend supported',source)

if __name__=='__main__': unittest.main()
