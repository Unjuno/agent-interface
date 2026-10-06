"""Retention-only byte/runtime verifier; no acquisition or diagnostic replay."""
import hashlib
import json
import pathlib

root=pathlib.Path(__file__).resolve().parent
freeze=json.loads((root/'FREEZE.json').read_bytes())
for name,digest in freeze['pins'].items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
native=root/'raw/v39-reader-e01-3cbf-native/record'
audit=root/'raw/v39-reader-e01-3cbf-audit/record'
receipt=json.loads((audit/'AUDIT.json').read_bytes())
assert receipt['status']=='PASS_SAVED_DIAGNOSTIC_AUDIT'
assert receipt['verdict']=='FINDING_PARSE_FAILURE_NOT_SURFACED'
assert set(receipt['hashes'])=={p.name for p in native.iterdir()}
for name,digest in receipt['hashes'].items():
    assert hashlib.sha256((native/name).read_bytes()).hexdigest()==digest,name
for original,export in [(native,root/'raw/v39-reader-e01-3cbf-native-export'),
                        (audit,root/'raw/v39-reader-e01-3cbf-audit-export')]:
    assert {p.name for p in original.iterdir()}=={p.name for p in export.iterdir()}
    for p in original.iterdir():
        assert p.read_bytes()==(export/p.name).read_bytes(),p.name
runtime=json.loads((root/'raw/container-inspect.json').read_bytes())
assert len(runtime)==2
for r in runtime:
    assert r['Image']==freeze['image']
    assert r['State']['ExitCode']==0 and not r['State']['OOMKilled'] and r['RestartCount']==0
    assert r['Config']['User']=='501:501'
    h=r['HostConfig']
    assert h['NetworkMode']=='none' and h['NanoCpus']==1000000000
    assert h['Memory']==536870912 and h['MemorySwap']==536870912 and h['PidsLimit']==64
    assert h['ReadonlyRootfs'] and h['CapDrop']==['ALL'] and h['SecurityOpt']==['no-new-privileges']
    assert {m['Destination']:m['RW'] for m in r['Mounts']}==({'/source':False,'/out':True} if 'native' in r['Name'] else {'/source':False,'/native':False,'/out':True})
manifest=root/'DELIVERY_MANIFEST.sha256'
if manifest.exists():
    pins={line.split('  ',1)[1]:line.split('  ',1)[0] for line in manifest.read_text().splitlines()}
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p!=manifest}
    assert actual==set(pins)
    for name,digest in pins.items():
        assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
print('PASS_RETENTION_ONLY: frozen source, nine native files, audit, exports, terminal runtime'+(', delivery manifest' if manifest.exists() else ''))
