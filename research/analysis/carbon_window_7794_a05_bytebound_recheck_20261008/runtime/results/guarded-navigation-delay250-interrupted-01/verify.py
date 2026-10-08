"""Audit preservation and incomplete status; never declare GUI success."""
import hashlib,json,sys,tarfile,tempfile
from pathlib import Path
root=Path(__file__).resolve().parent
sys.path.insert(0,str(root.parents[2]))
from runtime.integration_checks.host_timing import summarize

def check(value,message):
    if not value: raise ValueError(message)
manifest=json.loads((root/'manifest.json').read_text(encoding='utf-8-sig'))
raw={}
with tarfile.open(root/'raw.tar.gz') as archive:
    for member in archive.getmembers():
        check(member.isfile() and member.name in manifest and member.name not in raw,'member identity')
        data=archive.extractfile(member).read();spec=manifest[member.name]
        check(len(data)==spec['bytes'] and hashlib.sha256(data).hexdigest()==spec['sha256'],'hash')
        raw[member.name]=data
check(set(raw)==set(manifest),'closure')
prefix='results-local/guarded-navigation-delay250-primary-01/'
def read(name): return json.loads(raw[prefix+name])
check(read('transport/exit.json')['code']==1,'retained exit')
for name in ('finish.json','evaluation.json','evaluation-at-close.json','submission-history.jsonl','cleanup.json','transport/review-12.json'):
    check(prefix+name not in raw,'unexpected completion evidence')
for n in (5,10): check(read(f'transport/review-{n}.json')['phase']=='saved','declared saved review')
for n in (6,11):
    check(read(f'transport/review-{n}.json')['phase']=='destination-unconfirmed','unconfirmed navigation')
    check(read(f'transport/request-{n}.json')['arguments']['tail'][-1]=={'op':'wait_update','timeout_ms':250},'navigation delay')
artifact=raw['results-local/guarded-navigation-batch-build-01/runtime.pyz']
check(hashlib.sha256(artifact).hexdigest()=='5c1fe40d133a9f59a1e0367dafe8a4091347d797532cab8c329c87983a49d030','runtime identity')
with tempfile.TemporaryDirectory() as directory:
    for name,data in raw.items():
        if name.startswith(prefix+'transport/'):
            base=name[len(prefix+'transport/'):]
            check(Path(base).name==base,'flat filename')
            (Path(directory)/base).write_bytes(data)
    actual=summarize(directory)
check(actual==json.loads((root/'host-timing.json').read_text()),'timing reconstruction')
check(actual['timeline_status']=='partial' and actual['call_count']==12 and actual['returned_count']==12 and actual['transport_closed'] is False,'partial boundaries')
print(json.dumps({'preservation':'PASS','files':len(raw),'trial':'INTERRUPTED','independent_success':'UNVERIFIED'}))
