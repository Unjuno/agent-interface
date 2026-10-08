import hashlib,json
from pathlib import Path
p=Path(__file__).resolve().parent
f=json.loads((p/'FREEZE.json').read_text())
r=json.loads((p/'RESULT.json').read_text())
for name,want in f['source_sha256'].items():
 assert hashlib.sha256((p/name).read_bytes()).hexdigest()==want
assert r['main_commit']==f['main_commit']
assert r['scenario']==f['scenario']
assert r['exact_executor_method_result']=={'rejected':True,'reason':'latest observation sequence required before input','accepted_or_input_events':0}
assert r['decision']=='PASS_FAIL_CLOSED_NO_STALE_EXECUTOR_ADMISSION; SESSION_CONTINUITY_NOT_ESTABLISHED'
source=(p/'executor_v12.py').read_text()
assert source.index('expected_sequence != self.backend.sequence') < source.index('self.backend.validate(copied)')
assert 'if accepted["event"]!="accepted":raise RuntimeError(accepted)' in (p/'map01_overlap_controller_v39.py').read_text()
print('independent audit: PASS (4 frozen source hashes; exact stale-sequence rejection; zero acceptance/input events)')
