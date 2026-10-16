import hashlib
import tempfile
import unittest
from pathlib import Path
import reference as ref
from controls import run_controls
from saved_audit import load_cell

ROOT=Path(__file__).resolve().parent.parent/'source_deadline_probe_6067_b01_20261003_3cbf'

class SavedControls(unittest.TestCase):
    def test_fifteen_retained_controls_reject_with_original_unchanged(self):
        # The old saved cell has a different on-disk layout: create only a
        # derived test wrapper, never acquire or edit archived B01 bytes.
        raw=ROOT/'native-raw'
        before={str(p.relative_to(raw)):hashlib.sha256(p.read_bytes()).hexdigest()
                for p in raw.rglob('*') if p.is_file()}
        spec={'id':'b000','kind':'pulse','schedule':'fixed','offsets':[0]*4,'phase':0,'width_ms':20}
        with tempfile.TemporaryDirectory(prefix='a03-controls-') as folder:
            temp=Path(folder);derived=temp/'raw';cell=derived/'record/cells/b000';cell.mkdir(parents=True)
            for original in (raw/'record').iterdir():
                if original.is_file():(cell/original.name).write_bytes(original.read_bytes())
            (derived/'launch.json').write_bytes((raw/'launch.json').read_bytes())
            out=temp/'audit';out.mkdir()
            controls=run_controls(derived,ref.read(ROOT/'FREEZE.json'),{'rows':[spec]},out)
            self.assertEqual(len(controls),15)
            self.assertTrue(all(c['rejected'] is True for c in controls))
            self.assertEqual({c['name'] for c in controls},{'wait_bool','cpu_false','missing_wait',
                'post_after_paint','source_wait_id','pixel_hash','source_journal_id','observer_wait_index',
                'duplicate','wrong_source','wrong_rw','missing','extra','nonbind','bool_rw'})
            for trial in (out/'cell-controls').iterdir():load_cell(trial)
        after={str(p.relative_to(raw)):hashlib.sha256(p.read_bytes()).hexdigest()
               for p in raw.rglob('*') if p.is_file()}
        self.assertEqual(after,before)

if __name__=='__main__':unittest.main()
