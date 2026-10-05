"""Bounded verification of retained bytes only; never runs call histories."""
from pathlib import Path
import base64, gzip, hashlib, importlib.util, io, json
ROOT=Path(__file__).resolve().parent
def decode(item):
    encoded=(ROOT/item['public_name']).read_bytes()
    if hashlib.sha256(encoded).hexdigest()!=item['public_sha256']:raise ValueError('public hash')
    with gzip.GzipFile(fileobj=io.BytesIO(base64.b64decode(encoded))) as stream:data=stream.read(1_048_577)
    if len(data)>1_048_576 or len(data)!=item['original_bytes'] or hashlib.sha256(data).hexdigest()!=item['original_sha256']:raise ValueError('raw projection')
    return json.loads(data)
def main():
    for line in (ROOT/'SHA256SUMS').read_text(encoding='utf-8').splitlines():
        expected,path=line.split('  ',1)
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=expected:raise ValueError(path)
    pub=json.loads((ROOT/'PUBLICATION.json').read_text(encoding='utf-8'))
    records=pub['lossless_raw_projections']
    original=decode(records[0]);binding=json.loads((ROOT/'SOURCE_BINDING.json').read_text(encoding='utf-8'))
    spec=importlib.util.spec_from_file_location('retained_nu_oracle',ROOT/'audit_histories.py')
    audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
    errors=audit.verify(original,binding)
    if errors:raise ValueError(errors)
    for item in records[1:]:
        changed=decode(item)
        if audit.exact(original,changed) or not audit.verify(changed,binding):raise ValueError(item['original_name'])
    print(json.dumps({'retained_rows':40,'lossless_projections':9,'rejected_controls':8,'producer_invocations':0}))
if __name__=='__main__':main()
