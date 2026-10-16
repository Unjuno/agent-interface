import copy
import unittest
from pathlib import Path
import reference as ref
from evidence import admit_transport
ROOT=Path(__file__).resolve().parent.parent/'source_deadline_probe_6067_b01_20261003_3cbf'

class Custody(unittest.TestCase):
    def test_new_mode_requires_exact_prospective_match(self):
        raw=ROOT/'native-raw'
        freeze=ref.read(ROOT/'FREEZE.json');freeze['mode']='readiness'
        consumed=ref.read(raw/'consumed.json');consumed['mode']='readiness'
        launch=ref.read(raw/'launch.json');copied=ref.read(raw/'copy.json');after=ref.read(raw/'post_source.json')
        admit_transport(consumed,launch,copied,after,freeze)
        for mode in ('formal','source-boundary-diagnostic',False):
            c=copy.deepcopy(consumed);c['mode']=mode
            with self.assertRaises(ValueError):admit_transport(c,launch,copied,after,freeze)

if __name__=='__main__':unittest.main()
