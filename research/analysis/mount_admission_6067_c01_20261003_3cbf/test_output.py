import tempfile
import unittest
from pathlib import Path
from adapter import guard_output

class Output(unittest.TestCase):
    def test_disjoint_output_resolves(self):
        self.assertEqual(guard_output('/protected','/output/result','/source'),
                         (Path('/protected'),Path('/output/result')))
    def test_equal_beneath_and_source_overlap_rejected(self):
        for out in ('/protected','/protected/new','/source/new','/protected/nested/../new'):
            with self.subTest(out=out), self.assertRaises(ValueError): guard_output('/protected',out,'/source')
    def test_symlink_resolved_overlap_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);protected=root/'protected';protected.mkdir()
            alias=root/'alias';alias.symlink_to(protected,target_is_directory=True)
            with self.assertRaises(ValueError): guard_output(protected,alias/'new',root/'source')

if __name__=='__main__': unittest.main()
