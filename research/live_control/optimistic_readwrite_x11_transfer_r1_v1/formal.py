from __future__ import annotations
import json, platform, sys
from pathlib import Path
from run_case import run_case, SCENARIOS

ROOT=Path(__file__).resolve().parent
SCHEDULE=[]
for rep in range(3):
    order=SCENARIOS[rep:]+SCENARIOS[:rep]
    for j,scenario in enumerate(order):
        SCHEDULE.append({'case_id':f'f{rep}{j}-{scenario.lower()}', 'rep':rep, 'order_index':j, 'scenario':scenario})

def summarize(rows):
    by={s:[] for s in SCENARIOS}
    for row in rows: by[row['scenario']].append(row)
    gates={}
    gates['allocation']=len(rows)==12 and all(len(by[s])==3 for s in SCENARIOS)
    gates['complete']=all(r.get('error') is None and r.get('pass_case') and r.get('cleanup_workers_exited') and r.get('cleanup_xvfb_exited') for r in rows)
    gates['distinct_xids']=all(r.get('mapped_distinct_xids') and r.get('surface_xids',{}).get('A') != r.get('surface_xids',{}).get('B') for r in rows)
    ind=by['INDEPENDENT']
    gates['independent']=all(r.get('decision')=='PARALLEL' and r.get('final_effects')=={'A':'LOCAL1','B':'LOCAL1'} and r.get('final_receipts',{}).get('GLOBAL')==0 for r in ind)
    cand=by['SHARED_GLOBAL_CANDIDATE']
    gates['candidate_shared']=all(r.get('decision')=='SERIALIZE' and r.get('prepared_receipts',{}).get('GLOBAL')==0 and r.get('after_a_receipts',{}).get('GLOBAL')==1 and r.get('b_receipt_stale_after_a') is True and r.get('b_reprepare_count')==1 and r.get('final_receipts',{}).get('GLOBAL')==1 and r.get('final_effects',{}).get('B')=='G1' and not any(c.get('command',{}).get('value')=='G0' for c in r.get('owner_commands',[])) for r in cand)
    unsafe=by['SHARED_GLOBAL_SURFACE_ONLY']
    gates['surface_only_discriminator']=all(r.get('decision')=='PARALLEL_SURFACE_ONLY' and r.get('a_before_b_effect') is True and r.get('prepared_receipts',{}).get('GLOBAL')==0 and r.get('final_receipts',{}).get('GLOBAL')==1 and r.get('final_effects',{}).get('B')=='G0' for r in unsafe)
    stale=by['EXTERNAL_STALE']
    gates['external_stale']=all(r.get('decision')=='REVALIDATE' and r.get('changed_resources')==['B_LOCAL'] and r.get('b_effect_command_count')==0 and r.get('prepared_receipts',{}).get('B_LOCAL')==0 and r.get('final_receipts',{}).get('B_LOCAL')==1 and r.get('final_effects',{}).get('B')=='NONE' and not any(c.get('command',{}).get('op')=='set_effect' for c in r.get('owner_commands',[])) for r in stale)
    return by,gates

def main():
    rows=[]
    for spec in SCHEDULE:
        row=run_case(spec['case_id'],spec['scenario'])
        row['rep']=spec['rep']; row['order_index']=spec['order_index']
        rows.append(row)
        if row.get('error') is not None:
            break
    (ROOT/'FORMAL_ROWS.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n')
    by,gates=summarize(rows)
    passed=all(gates.values())
    out={
      'task':'OPTIMISTIC-READWRITE-X11-TRANSFER-R1-20260919-001',
      'formal_invocations':1,'reruns':0,'replacements':0,'tuning':0,
      'scheduled_cases':12,'rows':len(rows),
      'scenario_counts':{s:len(by[s]) for s in SCENARIOS},
      'gates':gates,
      'surface_only_stale_effects':sum(r.get('final_effects',{}).get('B')=='G0' for r in by['SHARED_GLOBAL_SURFACE_ONLY']),
      'candidate_stale_effects':sum(r.get('final_effects',{}).get('B')=='G0' for r in by['SHARED_GLOBAL_CANDIDATE']),
      'environment':{'python':sys.version.split()[0],'platform':platform.platform(),'xvfb':'private','effect_owner':'AF_UNIX+Tk'},
      'decision':'PASS_OPTIMISTIC_READWRITE_X11_TRANSFER_SCOPED' if passed else ('STOP_INCOMPLETE_FORMAL' if len(rows)!=12 else 'FAIL_OPTIMISTIC_X11_TRANSFER'),
      'pass':passed,
    }
    (ROOT/'RESULT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,sort_keys=True))
    raise SystemExit(0 if passed else 1)
if __name__=='__main__':main()
