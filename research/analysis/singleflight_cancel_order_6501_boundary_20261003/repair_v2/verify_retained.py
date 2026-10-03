"""Portable byte custody and copied-raw control verification; no candidate imports."""
import base64,gzip,hashlib,importlib.util,json
from pathlib import Path
from auditor_v2 import audit,EXPECTED_COUNTS,same_json
from controls_v2 import mutations
ROOT=Path(__file__).resolve().parent
def main():
    original=gzip.decompress(base64.b64decode((ROOT.parent/'run01/candidate-raw.json.gz.b64').read_bytes()))
    first=json.loads((ROOT/'first-characterization.json').read_bytes())
    assert hashlib.sha256(original).hexdigest()==first['original_raw_sha256']
    raw=json.loads(original);result=audit(raw)
    assert not result['errors'] and same_json(result['counts'],EXPECTED_COUNTS)
    spec=importlib.util.spec_from_file_location('frozen_auditor',ROOT.parent/'auditor.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    assert hashlib.sha256((ROOT.parent/'auditor.py').read_bytes()).hexdigest()==first['frozen_auditor_sha256']
    paths=list((ROOT/'controls').glob('*.json.gz.b64'))
    assert len(paths)==6
    assert {p.name.removesuffix('.json.gz.b64') for p in paths}=={r['name'] for r in first['controls']}
    for path in paths:
        data=gzip.decompress(base64.b64decode(path.read_bytes()))
        item=next(x for x in first['controls'] if x['name']==path.name.removesuffix('.json.gz.b64'))
        assert hashlib.sha256(data).hexdigest()==item['sha256']
        assert audit(json.loads(data))['errors'] and not old.audit(json.loads(data),raw['source_sha256'])['errors']
    controls=mutations(raw)
    assert len(controls)==14 and all(audit(value)['errors'] for _,value in controls)
    assert sum(not old.audit(value,raw['source_sha256'])['errors'] for _,value in controls)==6
    for line in (ROOT.parent/'PACKAGE-SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1)
        assert hashlib.sha256((ROOT.parent/name).read_bytes()).hexdigest()==digest,name
    print(json.dumps({'status':'PASS_PORTABLE_RETAINED_CUSTODY_V2','saved_copies':6,'effective_controls':14,'old_false_accepts':6,'assignments':192,'waiter_decisions':384,'formal_replayed':False},sort_keys=True))
if __name__=='__main__':main()
