import copy,json,unittest
from pathlib import Path
from audit_event import check

P=Path(__file__).resolve().parent


class AuditEventControls(unittest.TestCase):
 def test_original_and_nine_corruption_controls(self):
  raw=json.loads((P/'fixed-raw.json').read_bytes());fixtures=(P/'fixtures.json').read_bytes();source=(P/'source.py.txt').read_bytes()
  clean=check(raw,fixtures,source);self.assertEqual(clean['errors'],[]);self.assertEqual(clean['violations'],[])
  accepted=next(i for i,x in enumerate(raw['rows']) if x['status']=='returned');rejected=next(i for i,x in enumerate(raw['rows']) if x['status']=='exception')
  for change in ('row','identity','source','fixture','exception','output','mutation','field','scalar_type'):
   r=copy.deepcopy(raw)
   if change=='row':r['rows'].pop()
   elif change=='identity':r['rows'][0]['id']='foreign'
   elif change=='source':r['source_sha256']='0'*64
   elif change=='fixture':r['fixture_sha256']='0'*64
   elif change=='exception':r['rows'][rejected]['exception']='IndexError'
   elif change=='output':r['rows'][accepted]['output']['events'][0]['status']='succeeded'
   elif change=='mutation':r['rows'][0]['input_unchanged']=False
   elif change=='scalar_type':r['rows'][0]['input_unchanged']=1
   else:r['rows'][0]['extra']='fabricated'
   with self.subTest(change=change):
    result=check(r,fixtures,source);self.assertTrue(result['errors'] or result['violations'])


if __name__=='__main__':unittest.main()
