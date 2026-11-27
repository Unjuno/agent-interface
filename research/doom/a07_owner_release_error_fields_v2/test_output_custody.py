import json, os, subprocess, sys, tempfile, unittest
from pathlib import Path
from test_audit_a07_owner_release_reconciliation import fixture

class OutputCustodyTest(unittest.TestCase):
 def test_output_hardlink_does_not_modify_raw_evidence(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'raw'; runtime=root/'episode'/'runtime';runtime.mkdir(parents=True)
   events,owner=fixture(); raw=runtime/'events.jsonl'
   raw.write_text(''.join(json.dumps(row)+'\n' for row in events),encoding='utf-8')
   (runtime/'owner-events.json').write_text(json.dumps(owner),encoding='utf-8')
   before=raw.read_bytes();output=Path(t)/'result.json'
   try: os.link(raw,output)
   except OSError as exc: self.skipTest(f'hardlinks unavailable: {exc}')
   cmd=[sys.executable,'-B',str(Path(__file__).with_name('audit_a07_owner_release_reconciliation.py')),'--raw-dir',str(root),'--output',str(output)]
   completed=subprocess.run(cmd,check=False,capture_output=True)
   self.assertEqual(completed.returncode, 0, completed.stderr)
   self.assertEqual(raw.read_bytes(),before)
   self.assertEqual(json.loads(output.read_text())["status"], "PASS_CUSTODY_RECONCILED_SCOPED")