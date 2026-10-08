from __future__ import annotations
import argparse,copy,json
from pathlib import Path
import audit
def main():
 ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('batch_dir');ap.add_argument('--out',required=True);a=ap.parse_args()
 base=json.loads(Path(a.result).read_text()); controls=[]
 def test(name,mut):
  x=copy.deepcopy(base);mut(x);o=audit.verify(x,Path(a.batch_dir),regenerate=False);controls.append({'name':name,'rejected':not o['audit_pass'],'errors':o['errors']})
 test('fake_delta',lambda x:x.__setitem__('delta_pp',0.0))
 test('future_leak',lambda x:x['counters'].__setitem__('future',1))
 test('class_regression',lambda x:x['class_rates']['RECENT_DENSE'].__setitem__('query_rate',0.0))
 test('drop_manifest',lambda x:x['manifest'].pop())
 test('fake_decision',lambda x:x.__setitem__('decision','PASS_MATCHED_SOURCE_TEMPORAL_QUERY_BATCHED_SCOPED' if x['decision']!='PASS_MATCHED_SOURCE_TEMPORAL_QUERY_BATCHED_SCOPED' else 'HOLD_NO_SELECTION_DISCRIMINATOR'))
 assert all(c['rejected'] for c in controls),controls
 Path(a.out).write_text(json.dumps({'controls':controls,'rejected':sum(c['rejected'] for c in controls),'total':len(controls)},indent=2,sort_keys=True)+'\n')
 print(json.dumps(controls,indent=2))
if __name__=='__main__':main()
