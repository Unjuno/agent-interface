import json, pathlib
root=pathlib.Path(__file__).parent
f=json.loads((root/'fixture.json').read_text())

def sets(x): return set(x['read']),set(x['write'])
def conflict(x,y):
    rx,wx=sets(x); ry,wy=sets(y)
    return bool((wx & (ry|wy)) or (wy & rx))
def classify(a_tail,b_input,b_tail,unknown=False):
    if unknown: return 'SERIAL_UNKNOWN'
    if conflict(a_tail,b_input) or conflict(a_tail,b_tail): return 'SERIAL_CONFLICT'
    return 'OVERLAP_ELIGIBLE'
def omit_shared(section):
    z=json.loads(json.dumps(section))
    for p in z.values():
        p['read']=[r for r in p['read'] if r!='shared_file']
        p['write']=[r for r in p['write'] if r!='shared_file']
    return z
def alias_surfaces(section):
    z=json.loads(json.dumps(section))
    for p in z.values():
        p['read']=['surface_shared' if r in ('surface_A','surface_B') else r for r in p['read']]
        p['write']=['surface_shared' if r in ('surface_A','surface_B') else r for r in p['write']]
    return z

ind=f['independent']; shared=f['shared']
ind_cls=classify(ind['a_tail'],ind['b_input'],ind['b_tail'])
sh_cls=classify(shared['a_tail'],shared['b_input'],shared['b_tail'])
om=omit_shared(shared); om_cls=classify(om['a_tail'],om['b_input'],om['b_tail'])
al=alias_surfaces(ind); al_cls=classify(al['a_tail'],al['b_input'],al['b_tail'])
unknown_cls=classify(ind['a_tail'],ind['b_input'],ind['b_tail'],unknown=True)
obs=f['published_outcomes']
result={
 'pinned':f['pinned'],
 'classifications':{
   'independent':ind_cls,
   'shared':sh_cls,
   'unknown':unknown_cls,
   'omitted_shared_file_control':om_cls,
   'aliased_surface_control':al_cls
 },
 'published_outcomes':obs,
 'agreement':{
   'independent': ind_cls=='OVERLAP_ELIGIBLE' and obs['overlap_independent']==['A_DONE','B_DONE'],
   'shared': sh_cls=='SERIAL_CONFLICT' and obs['overlap_shared_negative']==['B_DONE','B_DONE'],
   'omitted_dependency_exposes_false_admission': om_cls=='OVERLAP_ELIGIBLE',
   'surface_alias_is_conservative': al_cls=='SERIAL_CONFLICT',
   'unknown_fails_closed': unknown_cls=='SERIAL_UNKNOWN'
 }
}
result['decision']='PASS_RESOURCE_FOOTPRINT_XTERM_TRANSFER_SCOPED' if all(result['agreement'].values()) else 'FAIL_RESOURCE_FOOTPRINT_XTERM_TRANSFER'
print(json.dumps(result,indent=2,sort_keys=True))
