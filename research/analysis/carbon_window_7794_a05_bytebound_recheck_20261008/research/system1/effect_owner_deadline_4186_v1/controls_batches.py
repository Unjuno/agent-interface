#!/usr/bin/env python3
import copy,json,pathlib,tempfile
import audit
from audit_batches import load

def main():
 rows,env_errors=load('formal2')
 if env_errors: raise SystemExit('baseline batch evidence invalid: '+repr(env_errors))
 out=[]
 def ch(name,mut):
  data=copy.deepcopy(rows); mut(data)
  with tempfile.TemporaryDirectory() as d:
   p=pathlib.Path(d); (p/'ROWS.json').write_text(json.dumps(data)); out.append({'name':name,'rejected':bool(audit.audit(p,3)['errors'])})
 ch('drop_row',lambda x:x.pop()); ch('duplicate_row',lambda x:x.append(copy.deepcopy(x[0]))); ch('authority',lambda x:x[0].update(authority=True)); ch('proposal_late',lambda x:x[0].update(proposal_ready_elapsed_ms=121.0)); ch('predispatch_late',lambda x:x[0].update(predispatch_elapsed_ms=121.0)); ch('app_exit',lambda x:x[0].update(app_exit=9)); ch('rep_bool',lambda x:x[0].update(rep=True))
 ch('sink_exit',lambda x:next(r for r in x if r['app_receipt']['type']=='APP_RESULT')['app_receipt'].update(sink_exit=9))
 ch('candidate_effect',lambda x:next(r for r in x if r['policy']=='SINK_PRECOMMIT_DEADLINE' and r['schedule']=='EARLY_LONG').update(effect_file={'case_id':'bad','sink_pid':0,'effect_ns':1}))
 ch('posthoc_launder',lambda x:next(r for r in x if r['policy']=='SINK_POSTHOC_CHECK' and r['schedule']=='NEAR_LONG')['app_receipt']['sink_receipt'].update(posthoc='ON_TIME'))
 ch('effect_identity',lambda x:next(r for r in x if r.get('effect_file'))['effect_file'].update(case_id='wrong'))
 ch('short_refuse',lambda x:next(r for r in x if r['policy']=='SINK_PRECOMMIT_DEADLINE' and r['schedule']=='EARLY_SHORT').update(effect_file=None))
 result={'controls':out,'all_rejected':all(v['rejected'] for v in out)}; pathlib.Path('CONTROLS2.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n'); print(json.dumps(result,sort_keys=True)); raise SystemExit(0 if result['all_rejected'] else 1)
if __name__=='__main__': main()
