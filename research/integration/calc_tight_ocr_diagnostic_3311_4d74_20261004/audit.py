import json,pathlib,hashlib
R=pathlib.Path(__file__).resolve().parent
raw=json.loads((R/'out/RAW.json').read_text(encoding='utf-8'));truth=json.loads((R/'ORACLE_HOST_ONLY.json').read_text(encoding='utf-8'));inputs={x['id']:x for x in json.loads((R/'INPUTS.json').read_text(encoding='utf-8'))};errors=[];results=[]
for row in raw:
 src=R/'inputs'/inputs[row['id']]['path']
 if hashlib.sha256(src.read_bytes()).hexdigest()!=row['source_sha256']:errors.append('source hash')
 for c in row['cells']:
  if 'argv' in c:
   p=R/'out'/pathlib.Path(c['argv'][1]).name
   if hashlib.sha256(p.read_bytes()).hexdigest()!=c['crop_sha256']:errors.append('crop hash')
   if c['end_ns']<c['start_ns']:errors.append('clock reversal')
 results.append(dict(id=row['id'],expected=truth[row['id']],actual=row['values'],match=truth[row['id']]==row['values']))
out=dict(disposition='HOLD_RECOGNITION_TRANSFER',scope='KNOWN_SAVED_IMAGE_DIAGNOSTIC_ONLY',errors=errors,rows=results,exact_rows=sum(r['match'] for r in results),total_rows=len(results),observed_native_runs=0,observed_model_calls=0)
with (R/'AUDIT.json').open('x',encoding='utf-8') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
