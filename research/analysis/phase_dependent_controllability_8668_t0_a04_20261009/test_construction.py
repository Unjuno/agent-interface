"""Pre-freeze, nonformal construction checks; writes no retained formal outputs."""
import json,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
import candidate,auditor
class Construction(unittest.TestCase):
 def test_frozen_cases_are_unique_and_cover_receipt_lifecycle(self):
  d=json.loads((ROOT/'design.json').read_text()); cases=d['scenarios']; ids=[x['id'] for x in cases]
  self.assertEqual(len(ids),len(set(ids)))
  required={'valid_pre_emit_cancel','prior_operation_cancel','same_id_prior_attempt_cancel','wrong_request_cancel','no_request_cancel_ack','valid_effect_confirmation','late_cancel_after_effect','effect_ack_without_effect','conflicting_post_emit_receipts','neutral_release_without_ack','duplicate_cancel_receipt'}
  self.assertTrue(required.issubset(ids))
 def test_bound_policy_preserves_valid_cancel_and_rejects_stale_ack(self):
  d=json.loads((ROOT/'design.json').read_text()); by={x['id']:x for x in d['scenarios']}
  valid=candidate.bound(by['valid_pre_emit_cancel'],d['active'])
  stale=candidate.bound(by['same_id_prior_attempt_cancel'],d['active'])
  self.assertEqual(valid['status'],'CANCELLED_NO_EFFECT'); self.assertTrue(valid['retry_eligible'])
  self.assertEqual(stale['status'],'PENDING'); self.assertFalse(stale['retry_eligible'])
  self.assertEqual(candidate.arrival_only(by['same_id_prior_attempt_cancel'])['status'],'CANCELLED_NO_EFFECT')
 def test_neutral_release_and_post_emit_cancel_never_admit_retry(self):
  d=json.loads((ROOT/'design.json').read_text()); by={x['id']:x for x in d['scenarios']}
  for name in ('neutral_release_without_ack','late_cancel_after_effect','conflicting_post_emit_receipts'):
   out=candidate.bound(by[name],d['active']); self.assertFalse(out['retry_eligible'],name)
 def test_auditor_reconstructs_preview_and_mutations(self):
  d=json.loads((ROOT/'design.json').read_text()); rows=[]
  for i,s in enumerate(d['scenarios']):
   b=candidate.bound(s,d['active']); a=candidate.arrival_only(s)
   rows.append({'schedule_id':f'a04-{i:03d}','exogenous':s,'request_bound':b,'arrival_type_only':a,'derived':{
    'bound_false_completion':b['status']=='EFFECT_CONFIRMED' and not s['effect_committed'],
    'bound_unsafe_retry':b['retry_eligible'] and (s['effect_committed'] or s['phase'] in ('EMITTED','CONSUMED') or not any(candidate.match_request(r,s['requests']) and r['kind']=='CANCEL_CONFIRMED_NO_EFFECT' for r in s['receipts'])),
    'arrival_false_completion':a['status']=='EFFECT_CONFIRMED' and not s['effect_committed'],
    'arrival_unsafe_retry':a['retry_eligible'] and (s['effect_committed'] or s['phase'] in ('EMITTED','CONSUMED') or not any(r['kind']=='CANCEL_CONFIRMED_NO_EFFECT' and r['operation_id']==d['active']['operation_id'] and r['attempt']==d['active']['attempt'] and candidate.match_request(r,s['requests']) for r in s['receipts']))
   }})
  raw={'schema':'8668-a04-raw-v1','allocation':candidate.RUN,'base_commit':candidate.BASE,'row_count':len(rows),'rows':rows}
  result=auditor.check(raw,d)
  self.assertEqual(result['errors'],[]); self.assertEqual(result['unsafe_bound_classifications'],0)
  self.assertGreater(result['accepted_safe_retries'],0); self.assertGreater(result['policy_differences'],0); self.assertGreaterEqual(len(result['binding_witnesses']),5)
  self.assertTrue(all(x['rejected'] for x in result['mutations']))
if __name__=='__main__': unittest.main()
