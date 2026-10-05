"""Independent integrity and outcome checks for this synthetic composition package."""
import hashlib, json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def read_json(p): return json.loads(p.read_text())
def rows(p): return [json.loads(line) for line in p.read_text().splitlines() if line.strip()]

def require(ok, message):
    if not ok: raise SystemExit('FAIL: ' + message)

manifest = read_json(HERE/'candidate-source-manifest.json')
for item in manifest['files']:
    p = HERE/'candidate-source'/item['path']
    data = p.read_bytes()
    require(hashlib.sha256(data).hexdigest() == item['sha256'], 'source SHA256 '+item['path'])
    blob = hashlib.sha1(f'blob {len(data)}\0'.encode()+data).hexdigest()
    require(blob == item['git_blob'], 'source Git blob '+item['path'])

events = rows(HERE/'raw/run/runtime/events.jsonl')
delivered = rows(HERE/'raw/run/runtime/delivered.jsonl')
obs = [x for x in delivered if x.get('event') == 'observation']
typed = [x for x in delivered if x.get('event') == 'typed_observation']
require(len(obs) == len(typed) == 5, 'five typed/full observations')
for a,b in zip(typed,obs):
    require(a['sequence'] == b['sequence'] and a['frame_rgb_sha256'] == b['frame_rgb_sha256'], 'typed/full sequence and artifact reconciliation')
    require(b['exact'] is True and b['artifact_ready_ns'] >= b['typed_ready_ns'], 'full artifact exact and post-typed')
release = [x for x in events if x.get('event') == 'input_release_transition']
admit = [x for x in events if x.get('event') == 'input_admission']
require(len(release) == len(admit) == 1, 'one admission and one release transition')
r = release[0]
receipt = r['owner_thread_keyup_receipt']
require(receipt['physical_key_measurement']['schema'] == 'keymap-batch-edge-v1', 'measurement adapter identity')
require(receipt['physical_key_measurement']['classification'] == 'CONFIRMED_PHYSICAL_UP', 'simulated classifier receipt')
require(receipt['physical_verification_authoritative'] is False, 'receipt is not authoritative physical verification')
trace = rows(HERE/'raw/fake-x-trace.jsonl')
require([x['event'] for x in trace] == [2,3], 'fake X key press then release')
require(trace[-1]['down_after'] == [], 'fake X keymap ends empty')
owner = read_json(HERE/'raw/run/runtime/owner-events.json')
require(any(x.get('event') == 'owner_explicit_keyup' and x.get('server_keyup_verified') for x in owner), 'owner reports fake-server keyup')
require(all(x.get('keys_down') == [] and x.get('buttons_down') == [] for x in owner if x.get('event') == 'owner_release'), 'owner cleanup samples empty')
score = read_json(HERE/'raw/run/runtime/score.json')
require(score.get('map_exit') is False and score.get('player_dead') is False, 'synthetic score preserved')
require((HERE/'raw/child.stderr').read_text() == '', 'child stderr empty')
require(any(x.get('event') == 'terminal' for x in events), 'terminal observed')
print(json.dumps({'result':'PASS_CONSTRUCTION_SCOPED','source_files':len(manifest['files']), 'typed_full_reconciled':5,
 'input_admission_release_pairs':1,'fake_x_edges':['KeyPress','KeyRelease'],'fake_x_final_down':[],
 'limitation':'All runtime input, game, capture and planner seams are synthetic; no live task-effect or physical claim.'},sort_keys=True))
