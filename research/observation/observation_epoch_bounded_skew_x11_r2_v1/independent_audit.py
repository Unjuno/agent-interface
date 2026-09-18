import argparse, json
from pathlib import Path

SKEW_NS=2_000_000

def classify(x):
    f=x['fields']; keys=('focus','target_binding','image','ui_context')
    ids=[(f[k]['session'],f[k]['surface'],f[k]['generation']) for k in keys]
    ts=[f[k]['sample_ns'] for k in keys]
    identity_ok=len(set(ids))==1
    focus_same=x['raw']['initial_focus']==x['raw']['final_focus']
    geom_same=tuple(x['raw']['initial_geometry'])==tuple(x['raw']['final_geometry'])
    anchor=max(ts)
    noncritical_ok=(anchor-f['image']['sample_ns']<=SKEW_NS and anchor-f['ui_context']['sample_ns']<=SKEW_NS)
    return identity_ok and focus_same and geom_same and noncritical_ok

def main():
    ap=argparse.ArgumentParser(); ap.add_argument('result'); ap.add_argument('--out',required=True); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text()); errors=[]
    for i,x in enumerate(r.get('rows',[])):
        exp=classify(x)
        if x.get('oracle')!=exp: errors.append(f'{i}:oracle')
        if x.get('candidate')!=exp: errors.append(f'{i}:candidate')
        ts=[x['fields'][k]['sample_ns'] for k in ('focus','target_binding','image','ui_context')]
        if not (ts[0]<=ts[1]<=ts[2]<=ts[3]<=x['raw']['revalidation_ns']): errors.append(f'{i}:clock_order')
        if x['raw']['image_bytes']!=1024: errors.append(f'{i}:image_bytes')
        if x['restored_focus']!=x['raw']['initial_focus']: errors.append(f'{i}:restore')
    o={'pass':not errors,'errors':errors[:100],'checked_rows':len(r.get('rows',[])),'method':'raw X11 readback/timestamp audit; imports no experiment implementation'}
    Path(a.out).write_text(json.dumps(o,indent=2,sort_keys=True)+'\n'); print(json.dumps(o,indent=2,sort_keys=True))
    raise SystemExit(0 if o['pass'] else 5)
if __name__=='__main__': main()
