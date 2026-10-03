import json,pathlib,hashlib
R=pathlib.Path('/data');O=pathlib.Path('/audit');raw=json.loads((R/'out/RAW.json').read_text());truth=json.loads((R/'ORACLE_HOST_ONLY.json').read_text());inputs={x['id']:x for x in json.loads((R/'candidate-input/INPUTS.json').read_text())};errors=[];rows=[]
for row in raw:
 p=R/'candidate-input/inputs'/inputs[row['id']]['path']
 if hashlib.sha256(p.read_bytes()).hexdigest()!=row['source_sha256']:errors.append('source hash')
 for c in row['cells']:
  crop=R/'out'/pathlib.PurePosixPath(c['argv'][1]).name
  if hashlib.sha256(crop.read_bytes()).hexdigest()!=c['crop_sha256'] or c['end_ns']<c['start_ns']:errors.append('crop or clock')
 rows.append(dict(id=row['id'],expected=truth[row['id']],actual=row['values'],match=truth[row['id']]==row['values']))
out={'disposition':'REJECT_FULL_BINARY_CANDIDATE; HOLD_INTEGRATION_RECOGNITION','scope':'Known retained images only, no live/heldout transfer or producer replay','errors':errors,'rows':rows,'exact_rows':sum(x['match'] for x in rows),'numeric_exact':sum(x['match'] for x in rows if x['expected'] is not None),'numeric_total':sum(x['expected'] is not None for x in rows),'blank_exact':sum(x['match'] for x in rows if x['expected'] is None),'ocr_attempts':sum(len(r['cells']) for r in raw),'ocr_elapsed_ns':sum(c['end_ns']-c['start_ns'] for r in raw for c in r['cells'])}
with (O/'AUDIT.json').open('x') as f:json.dump(out,f,indent=2)
print(json.dumps(out));raise SystemExit(bool(errors))
