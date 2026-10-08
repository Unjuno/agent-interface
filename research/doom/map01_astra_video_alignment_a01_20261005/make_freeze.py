import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
pkg=Path(__file__).resolve().parent
src=root/'research/doom/results/map01-astra-attempt-v1'
files=[src/'map01-astra-live-01-2x.mp4',src/'video.json',src/'events.jsonl',src/'report.json']+[src/f'frames/{i:02d}.png' for i in range(1,13)]
def h(p): return hashlib.sha256(p.read_bytes()).hexdigest()
d={'freeze_type':'retrospective source artifact manifest; not a prospective experiment freeze','video_metadata':json.loads((src/'video.json').read_text()),'inputs':{str(p.relative_to(root)):h(p) for p in files},'analysis_source_sha256':{n:h(pkg/n) for n in ['align.py','audit_alignment.py']}}
(pkg/'FREEZE.json').write_text(json.dumps(d,indent=2)+'\n')
