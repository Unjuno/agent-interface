import unittest
import coarse_model_dependency as coarse
import preflight_dependency as direct
from routing import choose_payload_aware,CLIPBOARD_EFFECTS

def mapping():
    rows=[[0,0] for _ in range(20)]
    rows[0]=[0xFFE1,0]
    rows[1]=[ord('a'),ord('A')]
    rows[2]=[ord('v'),ord('V')]
    return rows
class RoutingTest(unittest.TestCase):
    def test_representable_ascii_direct(self):
        d=choose_payload_aware('a',mapping(),8,frozenset());self.assertEqual(d.selected,'direct_keys');self.assertTrue(d.direct_preflight_ok)
    def test_representable_ascii_direct_even_clipboard_allowed(self):
        self.assertEqual(choose_payload_aware('a',mapping(),8,CLIPBOARD_EFFECTS).selected,'direct_keys')
    def test_gap_transparent_fails_closed(self):
        d=choose_payload_aware('@',mapping(),8,frozenset());self.assertIsNone(d.selected);self.assertEqual(d.coarse_selected,'direct_keys');self.assertFalse(d.direct_preflight_ok)
    def test_gap_clipboard_allowed_selects_clipboard_before_input(self):
        d=choose_payload_aware('@',mapping(),8,CLIPBOARD_EFFECTS);self.assertEqual(d.selected,'clipboard_utf8');self.assertEqual(d.coarse_selected,'direct_keys')
    def test_unicode_transparent_none(self):
        d=choose_payload_aware('β',mapping(),8,frozenset());self.assertIsNone(d.selected);self.assertIsNone(d.coarse_selected)
    def test_unicode_clipboard(self):
        d=choose_payload_aware('β',mapping(),8,CLIPBOARD_EFFECTS);self.assertEqual(d.selected,'clipboard_utf8');self.assertEqual(d.coarse_selected,'clipboard_utf8')
    def test_full_payload_preflight(self):
        d=choose_payload_aware('a@a',mapping(),8,frozenset());self.assertIsNone(d.selected);self.assertFalse(d.direct_preflight_ok)
if __name__=='__main__':unittest.main()
