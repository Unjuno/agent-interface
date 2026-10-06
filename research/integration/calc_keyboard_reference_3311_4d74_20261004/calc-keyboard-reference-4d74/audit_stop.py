import pathlib,json,hashlib
from saved_oracle import score_done
R=pathlib.Path(__file__).resolve().parent;P=json.loads((R/'PLAN.json').read_text());rows=[];errors=[]
for i in [1,2]:
 D=R/'runs'/('row'+str(i));r=json.loads((D/'raw.json').read_text());h=json.loads((D/'HOST_RECEIPT.json').read_text());scores=[]
 if r['source_hashes']!=P['source_hashes']:errors.append('source identity')
 for t in r['tasks']:scores.append({'label':t['label'],'score':score_done(D,t)})
 trial=r['tasks'][-1];receipt=trial['receipt']
 if i==2 and (receipt['status']!='refused' or receipt.get('program_emissions')!=0 or receipt.get('program_execution_started') is not False or receipt.get('error')!='BACKEND_CONSTRAINT'):errors.append('preinput refusal')
 if trial['physical']['keys'] or trial['physical']['buttons'] or r['cleanup_physical']['keys'] or r['cleanup_physical']['buttons']:errors.append('physical neutrality')
 rows.append({'row':i,'host_exit':h['exit_code'],'scores':scores,'trial_status':receipt['status'],'trial_emissions':receipt.get('program_emissions'),'detail':receipt.get('detail')})
out={'disposition':'STOP_KEY_ALIAS_BEFORE_KEYBOARD_TRIAL; H_UNTESTED','rows':rows,'errors':errors,'censored_rows':[2,3],'scope':'Saved records only; original producer not replayed. No causal/direct-vs-keyboard interpretation; initial direct trial and both primes remain independently scored.'}
with (R/'STOP_AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
