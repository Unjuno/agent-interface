import copy, hashlib, json, unittest
from pathlib import Path
from research.live_control.calc_compiled_receipt_v1 import map_receipt

HERE=Path(__file__).parent

def synthetic():
 return {'format':'decision-receipt-v4','reported_state':'terminal',
  'program_write_may_have_been_attempted':True,
  'terminals':[{'record':{'event':'terminal','status':'needs_decision',
   'decision_reason':'focus_changed','steps_completed':0,
   'release':{'verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[]}}}],
  'image':{'status':'image','relative_path':'frame.png','sha256':'a'*64}}

class ReceiptTests(unittest.TestCase):
 def test_real_modal_receipts_stop_without_replay(self):
  for stage in ('save','confirm'):
   with self.subTest(stage=stage):
    data=(HERE/'results'/'calc-table-live-01'/stage/'receipt.json').read_bytes()
    expected={'save':'8f5bd931d3f59f987435dd4d2f31f06f458a3828130e4472cbbfb22fca5f3a5c','confirm':'89bcba08379290faf6fa8befb199db54ebcfb137a268cfb646ae708f7cbfa885'}[stage]
    self.assertEqual(hashlib.sha256(data).hexdigest(),expected)
    r=map_receipt(json.loads(data))
    self.assertEqual(r['disposition'],'stop');self.assertEqual(r['delivery'],'unknown')
    self.assertFalse(r['replay_permitted']);self.assertEqual(r['completed_steps'],0)
    self.assertFalse(r['evidence']['fresh'])
 def test_explicit_empty_release_and_unknown_release(self):
  a=synthetic();self.assertEqual(map_receipt(a)['release'],'verified_empty')
  del a['terminals'][0]['record']['release']['keys_unknown']
  self.assertEqual(map_receipt(a)['release'],'unknown')
 def test_malformed_or_multiple_terminals_are_not_promoted(self):
  for mode in ('missing','multiple','nonempty','badstep','badflag'):
   with self.subTest(mode=mode):
    a=synthetic()
    if mode=='missing': a['terminals']=[]
    elif mode=='multiple': a['terminals'].append(copy.deepcopy(a['terminals'][0]))
    elif mode=='nonempty': a['terminals'][0]['record']['release']['keys_down']=['x']
    elif mode=='badstep': a['terminals'][0]['record']['steps_completed']=True
    else: a['program_write_may_have_been_attempted']='false'
    r=map_receipt(a);self.assertEqual(r['disposition'],'stop');self.assertFalse(r['replay_permitted'])
    if mode=='nonempty':self.assertEqual(r['release'],'unknown')
 def test_complete_does_not_claim_task_success(self):
  a=synthetic();a['terminals'][0]['record'].update(status='completed',decision_reason=None,steps_completed=1)
  r=map_receipt(a);self.assertIsNone(r['task_success']);self.assertFalse(r['replay_permitted'])
  a['program_write_may_have_been_attempted']=False
  self.assertEqual(map_receipt(a)['disposition'],'stop')