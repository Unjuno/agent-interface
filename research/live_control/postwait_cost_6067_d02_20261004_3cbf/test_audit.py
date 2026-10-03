"""Real saved-file consumer checks, not source-text or mock assertions."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from audit import check_cell
from test_cell import fixture

def saved_cell(root):
    spec,data=fixture()
    for key,name in [('source','source.json'),('capture','capture.json'),('epoch','epoch.json'),
                     ('fixture_ready','fixture-ready.json'),('observer_ready','observer-ready.json'),
                     ('display_ready','display-ready.json')]:
        (root/name).write_text(json.dumps(data[key]))
    (root/'spec.json').write_text(json.dumps(spec))
    for key,name in [('source_journal','source.jsonl'),('source_waits','source-waits.jsonl'),
                     ('frames','frames.jsonl'),('observer_waits','waits.jsonl')]:
        (root/name).write_text(''.join(json.dumps(row)+'\n' for row in data[key]))
    commands={
        'xvfb':['Xvfb','-displayfd','7','-screen','0','64x64x24','-nolisten','tcp','-noreset','-ac'],
        'fixture':['/usr/local/bin/python3','-B','/source/fixture.py','--display',':0',
                   '--cell',str(root/'spec.json'),'--out',str(root)],
        'observer':['/usr/local/bin/python3','-B','/source/observer.py','--display',':0',
                    '--window','7','--offsets',json.dumps([0,3,6,9]),'--out',str(root),
                    '--epoch-file',str(root/'epoch.json')]}
    hashes={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}
    receipt={'error':None,'spec':spec,'lifecycle':data['lifecycle'],'commands':commands,'files_sha256':hashes}
    (root/'cell.json').write_text(json.dumps(receipt)); return spec,receipt

class AuditTests(unittest.TestCase):
    def test_closed_saved_cell(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); spec,_=saved_cell(root)
            self.assertEqual(len(check_cell(root,spec)['events']),8)

    def test_actual_saved_byte_change_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); spec,_=saved_cell(root)
            (root/'source.json').write_text('{}')
            with self.assertRaises(ValueError): check_cell(root,spec)

    def test_unknown_saved_file_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); spec,_=saved_cell(root)
            (root/'extra.txt').write_text('extra')
            with self.assertRaises(ValueError): check_cell(root,spec)

    def test_observer_command_cannot_bind_foreign_display(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); spec,receipt=saved_cell(root)
            receipt['commands']['observer'][4]=':99'
            (root/'cell.json').write_text(json.dumps(receipt))
            with self.assertRaises(ValueError): check_cell(root,spec)

    def test_substituted_fixture_executable_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); spec,receipt=saved_cell(root)
            receipt['commands']['fixture'][2]='/different/fixture.py'
            (root/'cell.json').write_text(json.dumps(receipt))
            with self.assertRaises(ValueError): check_cell(root,spec)

if __name__=='__main__': unittest.main()
