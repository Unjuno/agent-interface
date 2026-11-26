import importlib.util,unittest
from test_map01_door_driver_protocol import pair
class Tests(unittest.TestCase):
 def setUp(self):
  self.assertIsNotNone(importlib.util.find_spec('map01_synthetic_exit_driver_protocol'))
  global SyntheticExitDriverProtocol
  from map01_synthetic_exit_driver_protocol import SyntheticExitDriverProtocol
 def test_binding_then_cover_and_one_final_action(self):
  for arm in ('control','use'):
   p=SyntheticExitDriverProtocol(arm)
   ready={'event':'ready','synthetic_exit_calibration':{'pwad_sha256':p.PWAD,'iwad_sha256':p.IWAD,'arm':arm,'scope':'synthetic calibration only'},'post_load_clock_gate':{'passed':True}}
   self.assertIsNone(p.receive(ready,1_000_000_000))
   for row in pair('initial',1,1_000_000_000):cmd=p.receive(row,1_100_000_000)
   self.assertEqual(cmd['id'],'cover-0')
   for seq,name in ((2,'cover-0'),(3,'exit-probe')):
    for row in pair(name,seq,1_000_000_000):p.receive(row,1_100_000_000)
    p.receive({'event':'terminal','id':name,'status':'completed'},1_100_000_000)
    cmd=p.receive({'event':'door_settle','operation_id':name,'status':'DONE'},1_100_000_000)
    if name=='cover-0':self.assertEqual(cmd['id'],'exit-probe')
    else:self.assertEqual(cmd,{'op':'finish'})
 def test_wrong_asset_never_enables_protocol(self):
  p=SyntheticExitDriverProtocol('use')
  with self.assertRaises(ValueError):p.receive({'event':'ready','synthetic_exit_calibration':{},'post_load_clock_gate':{'passed':True}},1)
if __name__=='__main__':unittest.main()
