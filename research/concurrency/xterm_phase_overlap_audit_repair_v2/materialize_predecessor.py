import base64,gzip,hashlib,io,pathlib,shutil,tarfile
root=pathlib.Path(__file__).parent
parent=root.parent/'xterm_phase_overlap_v1'
pins={
 'PREDECESSOR_RAW_CASES.json':'6426b6425764adc585585eff915faea504d1ddabac38ae34720660e277ce37f8',
 'PREDECESSOR_RESULT.json':'07c44477c1e1a4ebf032ebd6443bb2bc7d8b0fab8e5a1324b7500780182946e0',
 'PREDECESSOR_AUDIT.json':'2fa51e9e8f4c8830a1ab101d37922f1a3bd7272d3932ff4667402c562006ed75',
 'PREDECESSOR_SCHEDULE.json':'a87aee9a7eb3194b950c41f85a210683c4b7321767357b125ec595544fb50cd8',
}
raw=gzip.decompress(base64.b64decode((parent/'RAW_CASES.json.gz.b64').read_bytes()))
(root/'PREDECESSOR_RAW_CASES.json').write_bytes(raw)
shutil.copyfile(parent/'RESULT.json',root/'PREDECESSOR_RESULT.json')
shutil.copyfile(parent/'AUDIT.json',root/'PREDECESSOR_AUDIT.json')
gz=base64.b64decode((parent/'SOURCE_BUNDLE.tar.gz.b64').read_bytes())
tar=gzip.decompress(gz)
with tarfile.open(fileobj=io.BytesIO(tar),mode='r:') as tf:
    f=tf.extractfile('schedule.json')
    if f is None: raise SystemExit('schedule missing')
    (root/'PREDECESSOR_SCHEDULE.json').write_bytes(f.read())
for name,expected in pins.items():
    got=hashlib.sha256((root/name).read_bytes()).hexdigest()
    if got!=expected: raise SystemExit(f'{name} sha mismatch {got}')
print('materialized exact #1707 predecessor evidence')
