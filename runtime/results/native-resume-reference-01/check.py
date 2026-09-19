"""Read-only comparison on the retained original local run; no GUI allocation."""
import hashlib
import json
from pathlib import Path
from native_exchange_v1 import run

root = Path('results-local/native-direct-stdin-01').resolve(strict=True)
def snapshot():
    return {str(p.relative_to(root)): [hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_mtime_ns]
            for p in root.rglob('*') if p.is_file()}
before = snapshot()
decision = json.loads((root/'request-3.json').read_bytes())
digest = hashlib.sha256((root/'request-3.json').read_bytes()).hexdigest()
full = run(root, 3, decision, resume=True, compact=True)
ref = run(root, 3, resume=True, decision_sha256=digest, compact=True)
assert full['exchange']['resumed_read_only'] and ref['exchange']['resumed_read_only']
full.pop('exchange')
ref.pop('exchange')
assert full == ref
assert snapshot() == before
sizes = []
for stage in range(1,4):
    payload = (root/f'request-{stage}.json').read_bytes()
    common = {'run_directory':'results-local/native-direct-stdin-01','stage':stage,'resume':True}
    old = dict(common, decision=json.loads(payload))
    new = dict(common, decision_sha256=hashlib.sha256(payload).hexdigest())
    size = lambda value: len(json.dumps(value, ensure_ascii=False, separators=(',',':')).encode())
    sizes.append({'stage':stage,'full_decision_bytes':size(old),'digest_reference_bytes':size(new)})
print(json.dumps({'status':'PASS_SCOPED','unchanged_files':len(before),
    'same_complete_response_except_exchange_timestamps':True,
    'decision_sha256':digest,'image_sha256':ref['image_reference']['sha256'],
    'request_sizes':sizes,'new_gui_execution':False,'model_tokens_and_latency':'unmeasured'}, indent=2))
