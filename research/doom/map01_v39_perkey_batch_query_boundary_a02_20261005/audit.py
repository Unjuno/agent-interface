import hashlib,json
from pathlib import Path
here=Path(__file__).resolve().parent
freeze=json.loads((here/'FREEZE.json').read_text(encoding='utf-8-sig'))
lock=json.loads((here/'SOURCE_LOCK.json').read_text(encoding='utf-8-sig'))
assert hashlib.sha256((here/'probe.py').read_bytes()).hexdigest()==lock['candidate_probe_sha256']
assert freeze['source_sha256']==lock['source_sha256']
assert freeze['source_github_blob_sha']==lock['source_github_blob_sha']
r=json.loads((here/'results'/'a02'/'RESULT.json').read_text(encoding='utf-8'))
assert hashlib.sha256((here/'input_owner_v12.py').read_bytes()).hexdigest()==freeze['source_sha256']
assert r['source_sha256']==freeze['source_sha256']
seq,good,partial=r['runs']
assert seq['mode']=='sequential_per_key' and seq['final_down']==[]
assert [x['classification'] for x in seq['rows']]==['CONFIRMED_PHYSICAL_UP']*2
assert seq['keymap_query_count']==4 and seq['queries_between_up_injections']==2
assert good['mode']=='batched_boundary_samples' and good['final_down']==[]
assert [x['classification'] for x in good['rows']]==['CONFIRMED_PHYSICAL_UP']*2
assert good['keymap_query_count']==2 and good['queries_between_up_injections']==0
assert all(not x['grants_input_authority'] for x in good['rows'])
assert partial['mode']=='batched_boundary_samples' and partial['final_down']==[74]
assert [x['classification'] for x in partial['rows']]==['CONFIRMED_PHYSICAL_UP','RELEASE_UNCONFIRMED']
assert partial['rows'][0]['release_attempted'] and partial['rows'][1]['release_attempted'] and not partial['rows'][1]['injection_succeeded'] and not partial['rows'][1]['sync_succeeded']
assert partial['queries_between_up_injections']==0
print('AUDIT_PASS: normal per-key evidence and partial custody; inter-release query count 2 -> 0')
