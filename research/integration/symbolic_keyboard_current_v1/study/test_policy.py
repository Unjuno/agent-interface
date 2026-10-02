import json,subprocess,sys,unittest
from pathlib import Path
P=Path(__file__).with_name('policy.py')
def call(x):
 p=subprocess.run([sys.executable,str(P)],input=json.dumps(x),text=True,capture_output=True);return json.loads(p.stdout)
def row(policy,intent='UNDO',pm='EDITOR',cm='EDITOR',ph='a',ch='a'):
 return {'policy':policy,'intent':intent,'plan':{'mode':pm,'layout_hash':ph},'current':{'mode':cm,'layout_hash':ch}}
class T(unittest.TestCase):
 def test_raw(self):self.assertEqual(call(row('RAW_KEYSYM'))['decision'],'EMIT')
 def test_snap_current(self):self.assertEqual(call(row('SNAPSHOT_SYMBOLIC'))['decision'],'EMIT')
 def test_snap_layout(self):self.assertEqual(call(row('SNAPSHOT_SYMBOLIC',ph='a',ch='b'))['decision'],'REFUSE_STALE_LAYOUT')
 def test_snap_context(self):self.assertEqual(call(row('SNAPSHOT_SYMBOLIC',intent='CONFIRM',pm='MODAL',cm='EDITOR'))['decision'],'REFUSE_STALE_CONTEXT')
 def test_snap_bad_context(self):self.assertEqual(call(row('SNAPSHOT_SYMBOLIC',intent='CONFIRM'))['decision'],'REFUSE_CONTEXT')
 def test_current_layout(self):self.assertEqual(call(row('CURRENT_SYMBOLIC',ph='a',ch='b'))['decision'],'EMIT')
 def test_current_context_refuse(self):self.assertEqual(call(row('CURRENT_SYMBOLIC',intent='CONFIRM'))['decision'],'REFUSE_CONTEXT')
 def test_no_authority(self):self.assertFalse(call(row('CURRENT_SYMBOLIC'))['grants_action_authority'])
if __name__=='__main__':unittest.main()
