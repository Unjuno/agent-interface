import unittest
from audit_saved_v2 import materially_changed
class TypeMutationTests(unittest.TestCase):
    def test_bool_integer_is_real_json_change(self):
        self.assertTrue(materially_changed({'covered':True},{'covered':1}))
    def test_identical_copy_not_change(self):
        self.assertFalse(materially_changed({'covered':True},{'covered':True}))
    def test_ordinary_change(self):
        self.assertTrue(materially_changed({'epoch':'a'},{'epoch':'b'}))
if __name__=='__main__':unittest.main()
