"""Evidence corruption controls; no system/network fault injection."""
import copy,json,sys
from pathlib import Path
from audit import audit
out=Path(__file__).resolve().parent/sys.argv[1]
base=[json.loads(x) for x in (out/'samples.jsonl').read_text().splitlines()]
mutations={
'missing_row':lambda r:r.pop(),
'wrong_state_pixels':lambda r:r[0].update(state_pixels_sha256='0'*64),
'wrong_wire_hash':lambda r:r[0].update(wire_sha256='0'*64),
'wrong_sequence':lambda r:r[0].update(state_sequence=999),
'wrong_prior_state':lambda r:r[0].update(prior_pixels_sha256='0'*64),
'wrong_wire_length':lambda r:r[0].update(wire_bytes=r[0]['wire_bytes']+1),
'invalid_memory_measurement':lambda r:next(x for x in r if x['pass']==3).update(tracemalloc_peak=-1),
'wrong_input_route':lambda r:r[0].update(input='inputs/absent.png'),
'wrong_order':lambda r:r.reverse(),
'wrong_changed_tile_count':lambda r:r[0].update(changed_tiles=999),
}
baseline=audit(out)
assert not baseline['errors'], 'controls require passing unmodified baseline'
results=[]
for name,mutate in mutations.items():
 rows=copy.deepcopy(base);mutate(rows);a=audit(out,rows)
 results.append({'name':name,'rejected':bool(a['errors']),'errors':a['errors']})
coherent=copy.deepcopy(base)
for row in coherent:
 if row['pass']==3:
  row['tracemalloc_current']=0
  row['tracemalloc_peak']=100000 if row['arm']=='canonical' else 100
positive=audit(out,coherent)
assert not positive['errors'] and positive['allocation_decision']=='PASS_RETAINED_CAPTURE_ALLOCATION_BENEFIT', 'synthetic measurement positive control must pass'
target=next(x for x in coherent if x['pass']==3 and x['arm']=='streaming')
original_peak=target['tracemalloc_peak'];target['tracemalloc_peak']=10**9
a=audit(out,coherent)
results.append({'name':'coherent_allocation_boundary','synthetic_measurements_not_experimental':True,'rejected':not a['errors'] and a['decision']=='PASS_RETAINED_CAPTURE_WIRE_PARITY' and a['allocation_decision']=='HOLD_ALLOCATION_BENEFIT','positive_parity_decision':positive['decision'],'positive_allocation_decision':positive['allocation_decision'],'positive_changed_median_peak_ratio':positive['changed_median_peak_ratio'],'positive_all_peak_envelopes':positive['all_peak_envelopes'],'original_peak':original_peak,'altered_peak':target['tracemalloc_peak'],'parity_decision':a['decision'],'allocation_decision':a['allocation_decision'],'negative_all_peak_envelopes':a['all_peak_envelopes'],'errors':a['errors']})
receipt=json.loads((out.parent/(out.name+'.launch.json')).read_text());receipt['actual_exit']=17
a=audit(out,receipt_override=receipt)
results.append({'name':'wrong_process_exit','rejected':'process receipt' in a['errors'],'errors':a['errors']})
env=json.loads((out/'environment.json').read_text());env['as_limit']=[536870912,536870912]
a=audit(out,env_override=env)
results.append({'name':'wrong_address_space_bound','rejected':'resource bounds' in a['errors'],'errors':a['errors']})
receipt=json.loads((out.parent/(out.name+'.launch.json')).read_text());receipt['stdout_sha256']='0'*64
a=audit(out,receipt_override=receipt)
results.append({'name':'wrong_stdout_binding','rejected':'process log hashes' in a['errors'] and a['decision']=='STOP_PROVENANCE_OR_PROCESS','errors':a['errors']})
print(json.dumps({'controls':results,'all_rejected':all(x['rejected'] for x in results)},indent=2))
sys.exit(not all(x['rejected'] for x in results))
