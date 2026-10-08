import unittest
from policy import choose

class SelectionTests(unittest.TestCase):
    def test_unique_current_title_selects_only_matching_native_id(self):
        self.assertEqual(choose([{'id': 8, 'title': 'Other'}, {'id': 9, 'title': 'Target'}], ['title']), 9)
    def test_hidden_refuses(self):
        self.assertIsNone(choose([{'id': 8, 'title': None}, {'id': 9, 'title': None}], ['title']))
    def test_duplicate_refuses(self):
        self.assertIsNone(choose([{'id': 8, 'title': 'Target'}, {'id': 9, 'title': 'Target'}], ['title']))
    def test_full_conflicting_cues_refuses(self):
        self.assertIsNone(choose([{'id': 8, 'title': 'Target', 'parent': 'Other'}, {'id': 9, 'title': 'Other', 'parent': 'Target'}], ['title', 'parent']))
    def test_missing_field_refuses(self):
        self.assertIsNone(choose([{'id': 8}, {'id': 9, 'title': 'Target'}], ['title']))
    def test_boolean_id_refuses(self):
        self.assertIsNone(choose([{'id': True, 'title': 'Target'}, {'id': 9, 'title': 'Other'}], ['title']))
    def test_single_cue_cannot_see_unread_conflict(self):
        self.assertEqual(choose([{'id': 8, 'title': 'Target'}, {'id': 9, 'title': 'Other'}], ['title']), 8)

if __name__ == '__main__': unittest.main()
