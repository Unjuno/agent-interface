"""Explicit archive verification only: no source adapter or producer execution."""
import hashlib,importlib.machinery,importlib.util,json
from pathlib import Path
root=Path(__file__).resolve().parent
def require(condition,message):
    if not condition:raise ValueError(message)
for line in (root/'SHA256SUMS').read_text().splitlines():
    expected,path=line.split('  ',1)
    if hashlib.sha256((root/path).read_bytes()).hexdigest()!=expected:raise ValueError('archive hash mismatch:'+path)
publication=json.loads((root/'PUBLICATION.json').read_text())
mapped={x['original_relative_path']:x for x in publication['mapping']}
freeze=json.loads((root/'FREEZE.json').read_text())
for pin in freeze['files']:
    entry=mapped[pin['path']]
    require(entry['projection'] is None,'frozen source projection')
    data=(root/entry['archived_relative_path']).read_bytes()
    require(len(data)==pin['bytes'] and hashlib.sha256(data).hexdigest()==pin['sha256'],'frozen file binding')
loader=importlib.machinery.SourceFileLoader('archive_raw_audit',str(root/'audit.py.txt'))
spec=importlib.util.spec_from_loader(loader.name,loader);module=importlib.util.module_from_spec(spec);loader.exec_module(module)
raw_bytes=(root/'run-01'/'raw.json').read_bytes();raw=json.loads(raw_bytes)
errors,summary=module.audit(raw,freeze['cases'])
require(not errors,str(errors))
require(json.dumps(summary,sort_keys=True)==json.dumps(freeze['expected'],sort_keys=True),'frozen totals')
for row in raw:
    stem=row['case']['id'];folder=root/'run-01'
    stdout=(folder/(stem+'.stdout.bin')).read_bytes()
    stderr=(folder/(stem+'.stderr.jsonl')).read_bytes()
    require(stdout==bytes.fromhex(row['stdout_hex']),'native stdout')
    require(hashlib.sha256(stderr).hexdigest()==row['stderr_sha256'],'native stderr')
    require(json.dumps([json.loads(line) for line in stderr.splitlines()],sort_keys=True)==json.dumps(row['events'],sort_keys=True),'native event identity')
controls=sorted((root/'controls-01').glob('control-*.json'))
for path in controls:
    witness=json.loads(path.read_text())
    require(witness['raw_sha256']==hashlib.sha256(raw_bytes).hexdigest(),'control raw binding')
    mutant=json.loads(raw_bytes)
    if witness['operation']=='drop_last':mutant.pop()
    else:mutant[witness['row_index']]=witness['changed_row']
    canonical=json.dumps(mutant,sort_keys=True,separators=(',',':')).encode()
    require(hashlib.sha256(canonical).hexdigest()==witness['mutant_canonical_sha256'],'mutant binding')
    rejected,_=module.audit(mutant,freeze['cases'])
    require(rejected and rejected==witness['errors'],'control refusal')
require(len(controls)==8,'eight controls')
print(json.dumps({'disposition':'PASS_ARCHIVE_RAW_ONLY','summary':summary,'controls_rejected':len(controls),
                  'frozen_files':len(freeze['files']),'native_stream_pairs':len(raw)},sort_keys=True))
