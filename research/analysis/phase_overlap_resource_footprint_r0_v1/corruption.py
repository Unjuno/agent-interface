import json, pathlib
root=pathlib.Path(__file__).parent
base=json.loads((root/'RESULT.json').read_text())

def verify(r):
    c=r['counts']
    return (c['complete_mismatch']==0 and c['complete_admitted']>0 and
            c['declared_conflicts_serialized']==c['declared_conflicts_total'] and
            c['unknown_parallel_admissions']==0 and c['surface_only_mismatches']>0 and
            c['omitted_dependency_mismatches']>0 and c['reverse_predicate_mismatches']>0 and
            c['both_serial_orders_exercised']==2 and
            r['decision']=='PASS_PHASE_OVERLAP_RESOURCE_FOOTPRINT_SERIALIZABILITY_SCOPED')

mut=[]
for name,field,value in [
 ('inject_complete_mismatch','complete_mismatch',1),
 ('fail_open_unknown','unknown_parallel_admissions',1),
 ('erase_hidden_resource_discriminator','surface_only_mismatches',0),
 ('erase_omitted_dependency_discriminator','omitted_dependency_mismatches',0),
]:
    x=json.loads(json.dumps(base)); x['counts'][field]=value
    mut.append({'name':name,'rejected':not verify(x)})
out={'controls':mut,'pass':all(x['rejected'] for x in mut)}
print(json.dumps(out,indent=2,sort_keys=True))
raise SystemExit(0 if out['pass'] else 1)
