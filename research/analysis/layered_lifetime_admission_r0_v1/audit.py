import copy,json
from itertools import product
from pathlib import Path

LAYERS=('binding','precondition','route','observation_cache','motor_calibration')
ROUTE=2

def pop(bits):
    return {i for i in range(5) if bits&(1<<i)}

def expected():
    s={'rows':0,'layered_mismatch':0,'layered_stale_accept':0,'layered_false_invalidate':0,
       'global_stale_accept':0,'global_false_invalidate':0,'route_stale_accept':0,'route_false_invalidate':0}
    for d,c in product(range(1,32),range(32)):
        deps=pop(d); ch=pop(c); truth=not bool(deps&ch)
        layered=all(i not in ch for i in deps)
        glob=(c==0)
        route=not bool(c&(1<<ROUTE))
        s['rows']+=1
        s['layered_mismatch']+=layered!=truth
        s['layered_stale_accept']+=layered and not truth
        s['layered_false_invalidate']+=(not layered) and truth
        s['global_stale_accept']+=glob and not truth
        s['global_false_invalidate']+=(not glob) and truth
        s['route_stale_accept']+=route and not truth
        s['route_false_invalidate']+=(not route) and truth
    return {k:int(v) for k,v in s.items()}

def valid(r):
    if r.get('layers')!=list(LAYERS): return False
    if r.get('stats')!=expected(): return False
    if r.get('decision')!='PASS_LAYERED_LIFETIME_ADMISSION_CONTRACT_SCOPED': return False
    if (r.get('formal_invocations'),r.get('reruns'),r.get('replacements'),r.get('tuning'))!=(1,0,0,0): return False
    if len(r.get('directed',[]))!=5: return False
    for i,x in enumerate(r['directed']):
        if x.get('layer')!=LAYERS[i] or x.get('unchanged') is not True or x.get('oracle_unchanged') is not True:
            return False
        if x.get('same_layer_changed') is not False or x.get('oracle_changed') is not False:
            return False
    return True

def main():
    root=Path(__file__).resolve().parent
    r=json.loads((root/'RESULT.json').read_text())
    errors=[]
    if not valid(r): errors.append('primary')
    controls={}
    muts={
      'layered_mismatch':lambda x:x['stats'].__setitem__('layered_mismatch',1),
      'global_false_zero':lambda x:x['stats'].__setitem__('global_false_invalidate',0),
      'route_stale_zero':lambda x:x['stats'].__setitem__('route_stale_accept',0),
      'layer_identity':lambda x:x['layers'].__setitem__(4,'route'),
      'invocation':lambda x:x.__setitem__('formal_invocations',2),
      'decision':lambda x:x.__setitem__('decision','FAIL'),
    }
    for name,mut in muts.items():
        x=copy.deepcopy(r); mut(x); controls[name]=not valid(x)
    if not all(controls.values()): errors.append('corruption')
    out={'pass':not errors,'errors':errors,'corruption_controls':controls,'expected_stats':expected()}
    (root/'AUDIT.json').write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out['pass'] else 1)
if __name__=='__main__': main()
