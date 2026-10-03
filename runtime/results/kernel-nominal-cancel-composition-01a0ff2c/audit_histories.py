"""JSON-only expected transitions. Does not import producer/kernel/candidates."""
from pathlib import Path
from copy import deepcopy
import hashlib, json
ROOT = Path(__file__).resolve().parent
CASES = ['new','authorized_unbegun','begun_typed','begun_shaped_current','begun_shaped_stale','begun_missing','begun_unrelated','refused_begin','execution_none','execution_possible']
MISSING = {'begun_typed','begun_shaped_current','begun_shaped_stale','begun_missing','begun_unrelated'}
def exact(a,b):
    return json.dumps(a,sort_keys=True,separators=(',',':'),allow_nan=False)==json.dumps(b,sort_keys=True,separators=(',',':'),allow_nan=False)
def verify(raw, binding):
    errors=[]
    expected_keys={(f'n{n}u{u}',case) for n in (0,1) for u in (0,1) for case in CASES}
    rows=raw.get('rows',[])
    keys=[(r.get('arm'),r.get('case')) for r in rows]
    if len(keys)!=40 or len(set(keys))!=40 or set(keys)!=expected_keys: errors.append('coverage')
    if raw.get('schema')!='kernel-nominal-cancel-composition-v1': errors.append('schema')
    if raw.get('source_binding_sha256')!=hashlib.sha256((ROOT/'SOURCE_BINDING.json').read_bytes()).hexdigest(): errors.append('source-binding')
    arms={a['name']:a for a in binding['arms']}
    for row in rows:
        key=(row.get('arm'),row.get('case')); case=row.get('case'); arm=arms.get(row.get('arm'))
        if not arm or case not in CASES: errors.append(str(key)+':identity'); continue
        if not exact(row.get('nominal'),arm['nominal']) or not exact(row.get('uncertainty'),arm['uncertainty']) or row.get('lifecycle_sha256')!=arm['lifecycle_sha256']: errors.append(str(key)+':source')
        n,u=arm['nominal'],arm['uncertainty']
        expected_calls=[] if case=='new' else [('observe','returned'),('bind','returned'),('authorize','returned')]
        if case in MISSING or case.startswith('execution_'):expected_calls.append(('begin','returned'))
        if case=='refused_begin':expected_calls.append(('expired_begin','ContractError'))
        if case.startswith('execution_'):expected_calls.append(('execution','returned'))
        if case in {'begun_shaped_current','begun_shaped_stale','begun_missing','begun_unrelated'}:
            status = ('ContractError' if n else 'returned') if case=='begun_shaped_current' else ('ContractError' if n else 'AttributeError') if case=='begun_unrelated' else 'ContractError'
            expected_calls.append(('invalid_stop',status))
            if status!='returned':expected_calls.append(('valid_stop_after_refusal','returned'))
        else:expected_calls.append(('valid_stop','returned'))
        actual=[(c.get('call'),c.get('status')) for c in row.get('calls',[])]
        if not exact(actual,expected_calls):errors.append(str(key)+':calls')
        for c in row.get('calls',[]):
            if c.get('status')!='returned' and not exact(c.get('before'),c.get('after')):errors.append(str(key)+':refusal-mutated')
        effect=case=='execution_possible' or (case in MISSING and u)
        command='joint-command' if case in MISSING or case.startswith('execution_') else None
        expected={'stage':'stopped','reason':'joint-cancel','command_id':command,'effect_occurred':effect,'effect_verified':False,'release_verified':True}
        if row.get('outcome_status')!='returned' or not exact(row.get('outcome'),expected):errors.append(str(key)+':outcome')
    return errors
def main():
    data=(ROOT/'raw.json').read_bytes(); raw=json.loads(data)
    binding=json.loads((ROOT/'SOURCE_BINDING.json').read_text(encoding='utf-8'))
    errors=verify(raw,binding)
    controls=[]
    mutations=[
        lambda r:r['rows'][20].__setitem__('nominal',1),
        lambda r:r['rows'][32]['outcome'].__setitem__('effect_occurred',False),
        lambda r:r['rows'][30]['outcome'].__setitem__('effect_occurred',True),
        lambda r:r['rows'][33]['calls'][-2].__setitem__('status','returned'),
        lambda r:r['rows'][33]['calls'][-2]['after'].__setitem__('stop_reason','forged'),
        lambda r:r['rows'][38]['outcome'].__setitem__('effect_occurred',True),
        lambda r:r['rows'].pop(),
        lambda r:r['rows'][39].__setitem__('lifecycle_sha256','0'*64),
    ]
    for i,mutate in enumerate(mutations):
        changed=deepcopy(raw); mutate(changed)
        assert not exact(raw,changed),i
        found=verify(changed,binding)
        controls.append({'id':i,'errors':found,'rejected':bool(found)})
        (ROOT/f'control-{i}.json').write_text(json.dumps(changed,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    result={'errors':errors,'raw_sha256':hashlib.sha256(data).hexdigest(),'rows':len(raw['rows']),'controls':controls,'scope':'source-only ordinary engineering; no physical effect/release/current-tree certificate'}
    (ROOT/'audit.json').write_text(json.dumps(result,sort_keys=True,indent=2)+'\n',encoding='utf-8',newline='\n')
    print(json.dumps({'errors':errors,'rows':len(raw['rows']),'rejected_controls':sum(c['rejected'] for c in controls)}))
    raise SystemExit(0 if not errors and all(c['rejected'] for c in controls) else 1)
if __name__ == '__main__': main()
