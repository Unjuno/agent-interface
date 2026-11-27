"""Endpoint classification does not replace raw/provenance verification."""
import copy
import unittest
from map01_east_return_classification import classify_endpoint

def row(stage,x,y,angle,gap=92):
 return {'stage':stage,'status':'observed','position_x':x,'position_y':y,'angle':angle,'health':100,'death_count':0,'gap':gap,'physical_neutral_before_after':True,'last_action':[0.0]*9}

def valid():
 return [row('reverse-cross',648,-186,178),row('east-turn-1',640,-186,110),row('east-turn-2',635,-186,40),row('east-turn-3',630,-186,359),row('east-advance-1',740,-186,359),row('east-advance-2',800,-186,359)]

class EndpointClassificationTests(unittest.TestCase):
 def test_only_a_qualified_west_to_east_endpoint_is_observed(self):
  self.assertEqual(classify_endpoint(valid())['disposition'],'ENDPOINT_OBSERVED')
  for x in (752,900):
   rows=valid();rows[-1]['position_x']=x
   self.assertEqual(classify_endpoint(rows)['disposition'],'ENDPOINT_OBSERVED')
  for angle in (0,15,345):
   rows=valid();rows[-1]['angle']=angle
   self.assertEqual(classify_endpoint(rows)['disposition'],'ENDPOINT_OBSERVED')
  rows=valid();rows[-1]['position_x']=751
  self.assertEqual(classify_endpoint(rows)['disposition'],'MISS')
  rows=valid();rows[-1]['angle']=16
  self.assertEqual(classify_endpoint(rows)['disposition'],'MISS')
 def test_missing_unsafe_or_unqualified_evidence_is_hold(self):
  cases=[]
  rows=valid();rows[0]['position_x']=700;cases.append(rows)
  rows=valid();rows[0]['gap']=0;cases.append(rows)
  rows=valid();rows[2]['position_x']=901;cases.append(rows)
  rows=valid();rows[-1]['position_x']=float('nan');cases.append(rows)
  rows=valid();rows[3]['health']=0;cases.append(rows)
  rows=valid();rows[-1]['physical_neutral_before_after']=False;cases.append(rows)
  rows=valid();rows[-1]['last_action']=[False]*9;cases.append(rows)
  rows=valid();rows.pop(3);cases.append(rows)
  rows=valid();rows[2]['position_y']=-225;cases.append(rows)
  for rows in cases:
   with self.subTest(rows=rows):self.assertEqual(classify_endpoint(rows)['disposition'],'HOLD')
 def test_floor_is_explicitly_unmeasured(self):
  result=classify_endpoint(valid())
  self.assertEqual(result['player_floor_status'],'unmeasured')
  self.assertFalse(result['continuous_path_proven'])
if __name__=='__main__':unittest.main()
