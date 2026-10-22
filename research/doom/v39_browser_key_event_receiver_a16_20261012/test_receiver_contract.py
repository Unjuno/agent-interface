import re
import unittest
from pathlib import Path

PAGE = Path(__file__).with_name('index.html').read_text(encoding='utf-8-sig')

class BrowserReceiverContractTests(unittest.TestCase):
    def test_fixture_is_self_contained_and_local(self):
        self.assertNotRegex(PAGE, r'<script[^>]+src=')
        self.assertNotRegex(PAGE, r'<link[^>]+href=["\']https?://')
        self.assertIn('<title>Local key event receiver A16</title>', PAGE)

    def test_receiver_tracks_trusted_down_and_up_edges(self):
        self.assertIn("receiver.addEventListener('keydown'", PAGE)
        self.assertIn("receiver.addEventListener('keyup'", PAGE)
        self.assertIn('event.isTrusted', PAGE)
        self.assertIn('held.add(event.code)', PAGE)
        self.assertIn('held.delete(event.code)', PAGE)
        self.assertIn('event.preventDefault()', PAGE)

    def test_fixture_exposes_auditable_accessible_receipt(self):
        for marker in ['id="receiver"', 'id="held"', 'id="count"', 'id="events"', 'aria-live="polite"', 'snapshot()']:
            with self.subTest(marker=marker): self.assertIn(marker, PAGE)
        self.assertIn('document.activeElement.id', PAGE)

if __name__ == '__main__':
    unittest.main(verbosity=2)
