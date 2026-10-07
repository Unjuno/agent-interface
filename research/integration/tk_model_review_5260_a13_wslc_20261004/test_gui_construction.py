import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest

@unittest.skipUnless(os.name=='posix' and os.environ.get('DISPLAY'),'private Linux display required')
class GuiConstruction(unittest.TestCase):
    def test_real_xtest_receives_literal_keys_and_captures_frame(self):
        self.assertIsNotNone(importlib.util.find_spec('candidate'),'GUI candidate missing')
        from candidate import one
        with tempfile.TemporaryDirectory() as temp:
            row=one(Path(temp),dict(id='nonformal-construction',wanted='hzx',emitted='zx',recipient='target',geometry='600x300+50+50'),'construction-only')
            self.assertEqual(row['app']['target'],'zx')
            self.assertEqual(row['app']['decoy'],'')
            self.assertEqual([e['char'] for e in row['app']['events'] if e['kind']=='KeyPress'],['z','x'])
            self.assertTrue((Path(temp)/'screen.png').read_bytes().startswith(b'\x89PNG'))
            self.assertEqual(row['app_stderr'],'')
            self.assertEqual(row['app_exit'],0)

if __name__=='__main__':unittest.main()
