#!/usr/bin/env python3
import copy, json, sys
from pathlib import Path
from audit import audit_data

def main():
 p=Path(sys.argv[1]); reps=int(sys.argv[2]) if len(sys.argv)>2 else 3; original=json.loads(p.read_text()); base=p.parent
 intact=audit_data(copy.deepcopy(original),base,reps); tests=[{'name':'intact','rejected':False,'pass':not intact['errors']}]
 muts=[]
 def m(desc,fn): d=copy.deepcopy(original); fn(d); muts.append((desc,d))
 m('drop_row',lambda d:d['rows'].pop())
 m('duplicate_id',lambda d:d['rows'].__setitem__(1,{**d['rows'][1],'case_id':d['rows'][0]['case_id']}))
 m('false_motion',lambda d:d['rows'][0]['candidate'].__setitem__('motion_emitted',False))
 m('wrong_endpoint',lambda d:d['rows'][0]['candidate'].__setitem__('after',[30,30]))
 m('wrong_score',lambda d:d['rows'][0]['score'].__setitem__('target_hit',not d['rows'][0]['score']['target_hit']))
 si=next(i for i,r in enumerate(original['rows']) if r['policy']=='ROI_SNAP')
 m('roi_hash',lambda d:d['rows'][si]['candidate']['roi'].__setitem__('sha256','0'*64))
 m('candidate_exit',lambda d:d['rows'][0].__setitem__('candidate_exit',2))
 m('mask_after',lambda d:d['rows'][si]['candidate'].__setitem__('mask_after',1))
 m('policy_flip',lambda d:d['rows'][0].__setitem__('policy','ROI_SNAP' if d['rows'][0]['policy']=='DIRECT' else 'DIRECT'))
 m('scenario_flip',lambda d:d['rows'][0].__setitem__('scenario','ABSENT'))
 rejected=0
 for desc,d in muts:
  res=audit_data(d,base,reps); ok=bool(res['errors']) or not res['disposition'].startswith('PASS_'); rejected+=ok; tests.append({'name':desc,'rejected':ok})
 out={'schema':'color-roi-snap-controls-v1','intact_pass':tests[0]['pass'],'controls':len(muts),'rejected':rejected,'tests':tests}
 print(json.dumps(out,sort_keys=True,indent=2)); return 0 if out['intact_pass'] and rejected==len(muts) and len(muts)>=8 else 1
if __name__=='__main__': raise SystemExit(main())
