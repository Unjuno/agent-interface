import argparse, json
from pathlib import Path
SKEW_NS=2_000_000

def raw_truth(x):
    f=x['fields']; raw=x['raw']; keys=('focus','target_binding','image','ui_context')
    ids={(f[k]['session'],f[k]['surface'],f[k]['generation']) for k in keys}
    nc=max(f['image']['sample_ns'],f['ui_context']['sample_ns'])-min(f['image']['sample_ns'],f['ui_context']['sample_ns'])<=SKEW_NS
    return len(ids)==1 and raw['initial_focus']==raw['final_focus'] and tuple(raw['initial_geometry'])==tuple(raw['final_geometry']) and len(raw['focus_events'])==0 and nc

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out',required=True); a=ap.parse_args(); r=json.loads(Path(a.result).read_text()); errors=[]
    for i,x in enumerate(r.get('rows',[])):
        exp=raw_truth(x)
        if x.get('oracle')!=exp: errors.append(f'{i}:oracle')
        if x.get('generation_witnessed')!=exp: errors.append(f'{i}:candidate')
        if x['arm']=='FOCUS_ABA' and not x['raw']['focus_events']: errors.append(f'{i}:aba_event_missing')
        if x['arm']=='FOCUS_CHANGE' and not x['raw']['focus_events']: errors.append(f'{i}:change_event_missing')
        if x['arm'] in ('STABLE','PAINT_ONLY') and x['raw']['focus_events']: errors.append(f'{i}:stable_event')
        if x['raw']['image_bytes']!=1024: errors.append(f'{i}:image_bytes')
        if x['restored_focus']!=x['raw']['initial_focus']: errors.append(f'{i}:restore')
    o={'pass':not errors,'errors':errors[:100],'checked_rows':len(r.get('rows',[])),'method':'raw focus-event/readback audit; imports no experiment implementation'}
    Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True)); raise SystemExit(0 if o['pass'] else 5)
