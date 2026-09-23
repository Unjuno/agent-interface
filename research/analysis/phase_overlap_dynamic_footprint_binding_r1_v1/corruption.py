import json,pathlib,copy
r=json.loads((pathlib.Path(__file__).parent/'RESULT.json').read_text())
def verify(x):
 c=x['counts']; return (c['bound_mismatch']==0 and c['static_mismatch']==0 and c['unknown_admitted']==0 and c['bound_extra_over_static']>0 and c['bound_extra_safe']==c['bound_extra_over_static'] and c['bound_extra_mismatch']==0 and c['unbound_mismatch']>0 and c['bound_selector_write_admitted']==0 and x['decision']=='PASS_DYNAMIC_FOOTPRINT_BINDING_SERIALIZABILITY_SCOPED')
mut=[]
for name,field,val in [('inject_bound_mismatch','bound_mismatch',1),('fail_open_unknown','unknown_admitted',1),('erase_gain','bound_extra_over_static',0),('erase_unbound_discriminator','unbound_mismatch',0),('admit_selector_writer','bound_selector_write_admitted',1)]:
 x=copy.deepcopy(r); x['counts'][field]=val; mut.append({'name':name,'rejected':not verify(x)})
o={'controls':mut,'pass':all(m['rejected'] for m in mut)}; print(json.dumps(o,indent=2,sort_keys=True)); raise SystemExit(0 if o['pass'] else 1)
