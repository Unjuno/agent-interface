import argparse, copy, json, shutil, subprocess, sys, tempfile
from pathlib import Path

def mutate(raw, name):
    r = copy.deepcopy(raw)
    if name == 'drop': r['resource'].pop()
    elif name == 'duplicate': r['resource'].append(copy.deepcopy(r['resource'][0]))
    elif name == 'arm': r['resource'][0]['arm'] = 'MEMORYVIEW' if r['resource'][0]['arm'] == 'BASELINE' else 'BASELINE'
    elif name == 'cursor': r['resource'][0]['cursor_records'] = 123
    elif name == 'source':
        x = json.loads(r['resource'][0]['stdout']); x['source_sha256'] = '0'*64
        r['resource'][0]['stdout'] = json.dumps(x, separators=(',',':'))+'\n'
    elif name == 'result':
        x = json.loads(r['resource'][0]['stdout']); x['result']['authority'] = 'task'
        r['resource'][0]['stdout'] = json.dumps(x, separators=(',',':'))+'\n'
    elif name == 'inputsha':
        x = json.loads(r['resource'][0]['stdout']); x['input_sha256_after'] = '0'*64
        r['resource'][0]['stdout'] = json.dumps(x, separators=(',',':'))+'\n'
    elif name == 'exit': r['resource'][0]['exit'] = 7
    elif name == 'corpussha': r['corpus_sha256'] = '0'*64
    elif name == 'contract':
        x = json.loads(r['contracts'][0]['stdout']); x['rows'][0][1]['kind'] = 'error'
        x['rows'][0][1]['message'] = 'MUTATED'; r['contracts'][0]['stdout'] = json.dumps(x, separators=(',',':'))+'\n'
    return r

p = argparse.ArgumentParser(); p.add_argument('raw'); p.add_argument('--audit', required=True); p.add_argument('--out'); a = p.parse_args()
raw_path = Path(a.raw); source_dir = raw_path.parent
raw = json.loads(raw_path.read_text())
names = ['drop','duplicate','arm','cursor','source','result','inputsha','exit','corpussha','contract']
rows = []
for name in names:
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        for support in ('corpus.jsonl','INVOCATION.json','journal.jsonl','RAW.jsonl'):
            shutil.copyfile(source_dir/support,d/support)
        candidate = mutate(raw,name)
        (d/'RAW.json').write_text(json.dumps(candidate,sort_keys=True,indent=2)+'\n')
        cp = subprocess.run([sys.executable,'-B',a.audit,str(d/'RAW.json')],capture_output=True,text=True)
        try: audit = json.loads(cp.stdout)
        except Exception: audit = {}
        rejected = cp.returncode == 1 and audit.get('decision') == 'FAIL' and bool(audit.get('errors')) and not cp.stderr
        rows.append({'name':name,'rejected':rejected,'exit':cp.returncode,'audit_errors':audit.get('errors',[]),'stderr':cp.stderr})
result = {'schema':'reader-memoryview-controls-v2','rows':rows,'all_rejected':all(x['rejected'] for x in rows)}
text = json.dumps(result,sort_keys=True,indent=2)+'\n'
if a.out:
    with Path(a.out).open('x') as f: f.write(text); f.flush()
else: print(text,end='')
raise SystemExit(0 if result['all_rejected'] else 1)
