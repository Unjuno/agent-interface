import json,sys
p=sys.argv[1] if len(sys.argv)>1 else 'RESULT.json'; r=json.load(open(p))
errors=[]
if r.get('traces')!=250000: errors.append('trace_count')
if r.get('candidate_oracle_mismatches')!=0: errors.append('mismatch')
if r.get('retro_confirmation_escapes')!=0: errors.append('retro_escape')
if r.get('authority_grants')!=0 or r.get('task_input_grants')!=0: errors.append('authority')
if r.get('decision')!='PASS_RELEASE_CONFIRMATION_GENERATION_BINDING_SCOPED':errors.append('decision')
print(json.dumps({'errors':errors,'pass':not errors},sort_keys=True)); sys.exit(bool(errors))
