import argparse, hashlib, json, math, statistics
from pathlib import Path
RECORD_BYTES=256

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def unique(pairs):
 d={}
 for k,v in pairs:
  if k in d: raise ValueError('duplicate')
  d[k]=v
 return d
def invalid(x): raise ValueError('nonfinite')
def strict_load_line(b): return json.loads(b.decode(),object_pairs_hook=unique,parse_constant=invalid)
def expected_read(data, cursor_records,max_records=32):
 offset=cursor_records*RECORD_BYTES; seq=cursor_records+1; records=[]; tail='end'; problem=None
 if hashlib.sha256(data[:offset]).hexdigest()=='' : raise AssertionError
 while offset<len(data) and len(records)<max_records:
  end=data.find(b'\n',offset)
  if end<0: tail='incomplete'; break
  try: rec=strict_load_line(data[offset:end])
  except Exception: tail,problem='blocked','INVALID_JSON_RECORD'; break
  if not isinstance(rec,dict) or not isinstance(rec.get('event'),str) or not rec['event'] or rec.get('delivery_id')!=f'delivery:{seq}': tail,problem='blocked','INVALID_RECORD_OR_DELIVERY_SEQUENCE'; break
  records.append(rec); offset=end+1; seq+=1
 if len(records)==max_records and offset<len(data): tail='limit'
 return {'schema':'agent-interface/experimental-inbox-read-v1','records':records,'tail_state':tail,'problem':problem,'next_cursor':{'schema':'agent-interface/experimental-read-cursor-v1','stream_id':'formal-stream','offset':offset,'prefix_sha256':hashlib.sha256(data[:offset]).hexdigest(),'next_sequence':seq},'authority':'none','acknowledged':False,'input_dispatched':False}

def audit(raw_path):
 raw=json.loads(Path(raw_path).read_text()); root=Path(raw_path).parent; data=(root/'corpus.jsonl').read_bytes(); errors=[]; checks=0
 if hashlib.sha256(data).hexdigest()!=raw['corpus_sha256']: errors.append('corpus_sha'); checks+=1
 expected_count=(3*1*2 if raw['phase']=='construction' else 4*3*2)
 if len(raw['resource'])!=expected_count: errors.append('resource_count'); checks+=1
 groups={}
 for i,r in enumerate(raw['resource']):
  checks+=5
  if r['exit']!=0 or r['stderr']!='': errors.append(f'process:{i}')
  try: row=json.loads(r['stdout'])
  except Exception: errors.append(f'json:{i}'); continue
  if row['arm']!=r['arm'] or row['cursor_records']!=r['cursor_records']: errors.append(f'identity:{i}')
  expected_source = raw['source_sha256']['baseline_reader.py' if r['arm']=='BASELINE' else 'candidate_reader.py']
  if row.get('source_sha256') != expected_source: errors.append(f'source:{i}')
  if row['input_sha256_before']!=raw['corpus_sha256'] or row['input_sha256_after']!=raw['corpus_sha256']: errors.append(f'input:{i}')
  exp=expected_read(data,r['cursor_records'])
  if row['error'] is not None or row['result']!=exp: errors.append(f'result:{i}')
  groups[(r['cursor_records'],r['rep'],r['arm'])]=row
 for cur in sorted({r['cursor_records'] for r in raw['resource']}):
  if raw['phase']=='formal':
   for rep in range(3):
    a=groups[(cur,rep,'BASELINE')]; b=groups[(cur,rep,'MEMORYVIEW')]
    checks+=2
    if a['result']!=b['result']: errors.append(f'pair_result:{cur}:{rep}')
 # resource gates only formal
 metrics={}
 if raw['phase']=='formal':
  for cur in (0,2048,4064,4096):
   ratios=[]; wall=[]; cpu=[]
   for rep in range(3):
    a=groups[(cur,rep,'BASELINE')]; b=groups[(cur,rep,'MEMORYVIEW')]
    ratios.append(b['traced_peak_bytes']/a['traced_peak_bytes']); wall.append(b['wall_ns']/a['wall_ns']); cpu.append(b['cpu_ns']/a['cpu_ns'])
   metrics[str(cur)]={'peak_ratio_median':statistics.median(ratios),'peak_ratios':ratios,'wall_ratio_median':statistics.median(wall),'cpu_ratio_median':statistics.median(cpu),'baseline_peak':[groups[(cur,r,'BASELINE')]['traced_peak_bytes'] for r in range(3)],'candidate_peak':[groups[(cur,r,'MEMORYVIEW')]['traced_peak_bytes'] for r in range(3)]}
  for cur in (2048,4064):
   m=metrics[str(cur)]; checks+=9
   if not all(x<y for x,y in zip(m['candidate_peak'],m['baseline_peak'])): errors.append(f'peak_not_lower:{cur}')
   if m['peak_ratio_median']>0.75: errors.append(f'peak_ratio:{cur}')
   if m['wall_ratio_median']>1.20: errors.append(f'wall_guard:{cur}')
   if m['cpu_ratio_median']>1.20: errors.append(f'cpu_guard:{cur}')
 # contract parity/basic required outcomes
 if len(raw['contracts'])!=2: errors.append('contract_count')
 else:
  cs=[]
  for j,c in enumerate(raw['contracts']):
   checks+=2
   if c['exit']!=0 or c['stderr']!='': errors.append(f'contract_process:{j}'); continue
   try: cs.append(json.loads(c['stdout']))
   except: errors.append(f'contract_json:{j}')
  if len(cs)==2:
   checks+=10
   if cs[0]['rows']!=cs[1]['rows']: errors.append('contract_parity')
   by=dict(cs[0]['rows'])
   required={'incomplete':('result','incomplete'),'bad_json':('result','blocked'),'gap':('result','blocked'),'duplicate_key':('result','blocked'),'changed_prefix':('error','CURSOR_PREFIX_CHANGED'),'wrong_stream':('error','INVALID_CURSOR'),'bound':('error','STREAM_READ_BOUND_EXCEEDED')}
   for name,(kind,val) in required.items():
    got=by[name]
    if got['kind']!=kind: errors.append('contract_kind:'+name); continue
    if kind=='result' and got['value']['tail_state']!=val: errors.append('contract_tail:'+name)
    if kind=='error' and got['message']!=val: errors.append('contract_error:'+name)
 return {'schema':'reader-memoryview-audit-v1','checks':checks,'errors':errors,'metrics':metrics,'decision':('PASS_READER_MEMORYVIEW_HASH_SCOPED' if raw['phase']=='formal' and not errors else ('PASS_CONSTRUCTION' if raw['phase']=='construction' and not errors else 'FAIL'))}

if __name__=='__main__':
 p=argparse.ArgumentParser(); p.add_argument('raw'); a=p.parse_args(); out=audit(a.raw); print(json.dumps(out,sort_keys=True,indent=2)); raise SystemExit(0 if not out['errors'] else 1)
