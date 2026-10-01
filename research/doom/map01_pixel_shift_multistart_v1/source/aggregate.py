from __future__ import annotations
import argparse,json
from pathlib import Path

def wrap(x): return ((x+180)%360)-180
def span_for(rows):
    by_setup={}
    for r in rows: by_setup.setdefault(int(r['setup_right_pulses']),[]).append(float(r['reference_yaw']))
    consistency={str(k):max((abs(wrap(x-v[0])) for x in v),default=0.0) for k,v in by_setup.items()}
    if not all(k in by_setup for k in (0,12,24)): return {'span_deg':None,'relative_deg':{},'within_setup_max_delta_deg':consistency}
    base=by_setup[0][0]; rel={str(k):wrap(v[0]-base) for k,v in by_setup.items()}; vals=[rel[str(k)] for k in (0,12,24)]
    return {'span_deg':max(vals)-min(vals),'relative_deg':rel,'within_setup_max_delta_deg':consistency}
def main(plan,root,ledger):
    p=json.loads(plan.read_text()); l=json.loads(ledger.read_text())
    ids=[c['id'] for c in p['cases']]
    if sorted(l.get('completed',{}))!=sorted(ids) or l.get('failed') or l.get('started'): raise RuntimeError(('allocation incomplete',l))
    results=[json.loads((root/c['id']/'result.json').read_text()) for c in p['cases']]
    main_rows=[r for r in results if r['kind']=='main']; aligned=[r for r in results if r['kind']=='aligned']; missing=[r for r in results if r['kind']=='missing_reference']
    span={str(seed):span_for([r for r in main_rows if r['seed']==seed]) for seed in (996301,996302)}; span['996303']=span_for(aligned)
    reference_diversity=all(v['span_deg'] is not None and v['span_deg']>=90.0 and all(d<=0.25 for d in v['within_setup_max_delta_deg'].values()) for v in span.values())
    nonzero=[r for r in main_rows if int(r['setup_right_pulses'])>0]
    releases_ok=True
    for r in results:
        releases=[x for x in r['owner_records'] if isinstance(x,dict) and x.get('event')=='owner_release']; expected=int(r['setup_input_program_count'])+int(r['scored_input_program_count'])
        if len(releases)!=expected or any(x.get('verified') is not True or x.get('keys_down')!=[] or x.get('buttons_down')!=[] for x in releases): releases_ok=False
    gates={
      'main_12of12_matched_within6':len(main_rows)==12 and all(r['terminal_status']=='MATCHED' and r['within_6deg'] for r in main_rows),
      'main_no_false_matched':not any(r['false_matched'] for r in main_rows),
      'nonzero_headings_8of8':len(nonzero)==8 and all(r['terminal_status']=='MATCHED' and r['within_6deg'] for r in nonzero),
      'reference_span_ge90_each_block':reference_diversity,
      'aligned_3of3_zero':len(aligned)==3 and all(r['terminal_status']=='MATCHED' and r['correction_pulses']==0 and r['scored_input_program_count']==0 for r in aligned),
      'missing_unknown_zero_correction':len(missing)==1 and missing[0]['terminal_status']=='UNKNOWN_MISSING_REFERENCE' and missing[0]['correction_pulses']==0,
      'release_and_neutral':releases_ok and all(not any(r['neutral_keymap'].values()) and r['owned_keys_final']==[] for r in results),
      'zero_deaths':all(r['death_count']==0 for r in results),
    }
    if not (gates['release_and_neutral'] and gates['aligned_3of3_zero'] and gates['missing_unknown_zero_correction'] and gates['zero_deaths']): decision='FAIL_INTEGRITY'
    elif any(r['false_matched'] for r in main_rows): decision='FAIL_PIXEL_SHIFT_MULTISTART'
    elif not reference_diversity: decision='HOLD_REFERENCE_DIVERSITY_NOT_REALIZED'
    elif all(gates.values()): decision='PASS_PIXEL_SHIFT_MULTISTART_SCOPED'
    else: decision='HOLD_CROSS_SCENE_TRANSFER'
    summary={'schema':'map01-pixel-shift-multistart-formal-a2-v1','task':p['task'],'decision':decision,'gates':gates,'reference_heading_spans':span,'cases':results,'formal_case_invocations':16,'same_id_reruns':0,'supervision':'one case per outer invocation'}
    (root/'summary.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n'); print(json.dumps({'decision':decision,'gates':gates,'reference_heading_spans':span},indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--plan',type=Path,required=True);ap.add_argument('--root',type=Path,required=True);ap.add_argument('--ledger',type=Path,required=True);a=ap.parse_args();main(a.plan,a.root,a.ledger)
