import unittest
from tree_custody import assert_manifest

class TreeCustody(unittest.TestCase):
    def test_exact_content_and_file_set(self):
        assert_manifest({'cell/source.json':'1'*64},{'cell/source.json':'1'*64},'identity')
    def test_substitution_missing_extra_and_mistyped_hash_rejected(self):
        expected={'cell/source.json':'1'*64}
        for changed in ({'cell/source.json':'2'*64},{},{**expected,'other':'3'*64},
                        {'cell/source.json':False}):
            with self.assertRaises(ValueError):assert_manifest(changed,expected,'exact custody')

if __name__=='__main__':unittest.main()
