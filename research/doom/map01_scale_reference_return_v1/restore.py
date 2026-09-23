"""Read-only source/decision restoration. Does NOT verify pixels or native receipts."""
import base64,hashlib,io,json,lzma,sys,tarfile
from pathlib import Path
here=Path(__file__).resolve().parent
out=Path(sys.argv[1]) if len(sys.argv)>1 else Path('restored-scale-reference')
if out.exists():raise SystemExit('refuse existing output')
meta=json.loads((here/'PUBLICATION.json').read_text())
def verify(data,expected):
    if hashlib.sha256(data).hexdigest()!=expected:raise SystemExit('hash mismatch')
source=lzma.decompress(base64.b64decode((here/'source.tar.xz.b64').read_text().strip(),validate=True))
xz=base64.b64decode((here/'source.tar.xz.b64').read_text().strip(),validate=True)
verify(xz,meta['source_archive_sha256'])
wtext=(here/'decision-witness.json.xz.b64').read_bytes();verify(wtext,meta['decision_witness']['text_sha256'])
raw=lzma.decompress(base64.b64decode(wtext.strip(),validate=True));verify(raw,meta['decision_witness']['raw_sha256'])
w=json.loads(raw);summary=json.loads((here/'SUMMARY.json').read_text())
assert [r['case'] for r in w['rows']]==[f'case-{i:02d}' for i in range(10)]
assert sum(len(r['observations']) for r in w['rows'])==50
for r in w['rows']:
    assert sum(o['action'] in ('Left','Right') for o in r['observations'])==r['pulses']
    if r['reason']=='VISUAL_ALIGNED':
        assert r['final_yaw_error_deg']<=3 and len(r['observations'])>=2
        assert all(o['match']['status']=='FOUND' and abs(o['match']['error_x_px'])<=12 for o in r['observations'][-2:])
scaled=[r for r in w['rows'] if r['policy']=='scaled' and r['stratum'] in ('small','large')]
assert sum(r['reason']=='VISUAL_ALIGNED' for r in scaled)==summary['scaled_main_success']==3
assert summary['decision']=='HOLD_MATCHER_RANGE'
out.mkdir(parents=True)
with tarfile.open(fileobj=io.BytesIO(source),mode='r:') as t:t.extractall(out/'source',filter='data')
freeze=json.loads((out/'source/FREEZE.json').read_text())
for name,h in freeze['sha256'].items():verify((out/'source'/name).read_bytes(),h)
(out/'decision-witness.json').write_bytes(raw)
print('PASS_SOURCE_AND_DECISION_RESTORATION; full PNG/input audit requires the separate evidence archive')
