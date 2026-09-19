from __future__ import annotations
import argparse,json
from pathlib import Path
PASS='PASS_LIVE_CAUSAL_EFFECT_SAMPLE_SAME_PROCESS_X11_SCOPED'

def classify(r):
    eff=[x for x in r['rows'] if x['arm']=='V12_EFFECT'];ctl=[x for x in r['rows'] if x['arm']=='NO_ACTION_CONTROL']
    if len(eff)!=6 or len(ctl)!=6:return 'FAIL_INTEGRITY'
    for x in r['rows']:
        if x.get('exceptions') or x.get('controller_errors'):return 'FAIL_V12_LIVE_CONTROL_REGRESSION'
        sc=x.get('supervisor_cleanup',{})
        if sc.get('child_exit_code')!=0 or sc.get('clients_exit_before_server_stop') is not True or sc.get('socket_exists_after_server_stop') is not False:return 'FAIL_V12_LIVE_CONTROL_REGRESSION'
    for x in eff:
        events=[(e.get('kind'),e.get('key')) for e in x.get('application_events',[])]
        if events!=[('KeyPress','F8'),('KeyRelease','F8')] or x.get('terminal_key_down') is not False:return 'FAIL_V12_LIVE_CONTROL_REGRESSION'
        try:
            act=x['composition']['actuation'];er=x['effect_records']
            if x['composition']['status']!='COMPOSED_PHYSICAL_ACTUATION':return 'FAIL_V12_LIVE_CONTROL_REGRESSION'
            if len(er)!=1 or not act['actuation_id'] or er[0]['actuation_id']!=act['actuation_id']:return 'FAIL_EFFECT_PROVENANCE'
            if not (x['pre_score']['red_centroid_x']<100 and x['post_score']['red_centroid_x']>180):return 'FAIL_EFFECT_INDEPENDENT_SCORE'
            if x.get('clock_disposition')!='useful_bound':return 'FAIL_EFFECT_TEMPORAL_OR_CLOCK'
            e=x['temporal_analysis']['effects']
            if e.get('useful_bound')!=1 or any(v for k,v in e.items() if k!='useful_bound'):return 'FAIL_EFFECT_TEMPORAL_OR_CLOCK'
            dm=x['down_result']['physical_key_measurement'];um=x['up_result']['physical_key_measurement']
            if dm.get('grants_input_authority') or um.get('grants_input_authority') or x['composition'].get('grants_input_authority'):return 'FAIL_INTEGRITY'
            if er[0]['t_ns']<act['down_hi']:return 'FAIL_EFFECT_TEMPORAL_OR_CLOCK'
        except Exception:return 'FAIL_INTEGRITY'
    for x in ctl:
        if not (x.get('pre_score',{}).get('red_centroid_x',999)<100 and x.get('post_score',{}).get('red_centroid_x',999)<100):return 'FAIL_EFFECT_INDEPENDENT_SCORE'
        if x.get('effect_records') or x.get('application_events'):return 'FAIL_EFFECT_INDEPENDENT_SCORE'
    return PASS

def main():
    ap=argparse.ArgumentParser();ap.add_argument('result');ap.add_argument('--out',required=True);a=ap.parse_args();r=json.loads(Path(a.result).read_text());errors=[]
    if r.get('task')!='P0-LIVE-CAUSAL-EFFECT-X11-DIAGNOSTIC-A3-20260918-003':errors.append('task')
    if r.get('phase')!='formal' or r.get('formal_invocations')!=1 or r.get('reruns')!=0:errors.append('invocation')
    if r.get('science_runner_blob')!='d8c509a55fe5363dc5211aebe510a720e964f7f3':errors.append('science_source')
    if len(r.get('rows',[]))!=12:errors.append('sessions')
    decision=classify(r)
    if errors and decision==PASS:decision='FAIL_INTEGRITY'
    out={'decision':decision,'errors':errors,'pass':decision==PASS and not errors,'sessions':len(r.get('rows',[]))}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+'\n');print(json.dumps(out,sort_keys=True))
if __name__=='__main__':main()
