"""Independent read-only audit of A03 delayed-gate evidence; no experiment execution."""
import hashlib, json
from pathlib import Path
PKG=Path(__file__).resolve().parent

def load(path): return json.loads((PKG/path).read_text(encoding='utf-8-sig'))
def sha(path): return hashlib.sha256((PKG/path).read_bytes()).hexdigest()
freeze=load('FREEZE-A03-CONTROL-V3.json')
for item in freeze['locked_files']:
    p=PKG/item['path']
    assert p.stat().st_size==item['bytes'], item['path']
    assert sha(item['path'])==item['sha256'], item['path']
assert sha('results/a03_v3/RESULT.json')==freeze['candidate_result_sha256']
result=load('results/a03_control_supplement_v3/RESULT.json')
stdout=json.loads((PKG/'TOOL_STDOUT_A03_CONTROL_V3_CAPTURE.txt').read_text(encoding='utf-8-sig'))
assert stdout==result, 'captured stdout differs from saved structured result'
assert result['schema']=='v39-owner-timeout-post-bound-control-supplement-v1'
prior=load('results/a03_v3/RESULT.json')
assert result['candidate']==prior['candidate'], 'candidate was not reused byte-semantically'
assert result['base_main']==freeze['base_main']

def delay(arm): return arm['timing']['sync_gate_open_ns']-arm['timing']['timeout_return_ns']
for arm in (result['control'],result['candidate']):
    assert 1_700_000_000 <= delay(arm) <= 1_900_000_000
    assert arm['terminal']=={'status':'failed','release_verified':False}
    assert arm['physical_empty'] is True
    assert arm['owner_stopped_after_terminal'] is True
    assert arm['up_rows']==[]
    assert arm['bridge_held']==['F8']
    assert arm['bridge_events']==['accepted','step_started','input_admission','terminal']
    assert arm['event_after_terminal'] is False
    assert arm['owner_releases'][0]=={'reason':'expired','verified':True,'keys_down':[],'buttons_down':[],'per_key_classifications':['CONFIRMED_PHYSICAL_UP']}
control=result['control']
candidate=result['candidate']
assert 'owner_stopped_within_bound' not in control['timing']
assert candidate['timing']['owner_stopped_within_bound'] is False
wait=candidate['timing']['late_drain_wait_ns']
assert wait >= 1_500_000_000
assert candidate['timing']['sync_gate_open_ns'] > candidate['timing']['timeout_return_ns'] + wait
assert (PKG/'TOOL_STDOUT_A03_CAPTURE.txt').is_file()
assert (PKG/'TOOL_STDOUT_A03_V2_CAPTURE.txt').is_file()
assert (PKG/'CONSTRUCTION-A03-V1.md').is_file()
assert (PKG/'CONSTRUCTION-A03-V2.md').is_file()
print(json.dumps({'disposition':'FAIL_POST_BOUND_LATE_RELEASE_NOT_DRAINED','baseline_gate_delay_ns':delay(control),'candidate_gate_delay_ns':delay(candidate),'candidate_late_drain_wait_ns':wait,'candidate_wait_over_nominal_ns':wait-1_500_000_000,'both_terminal_failed_unverified':True,'both_bridge_stale_F8':True,'both_later_physical_up_confirmed':True,'candidate_up_rows':0,'stdout_capture_complete':True,'candidate_reused_not_rerun':True,'scope':'fake-display delayed-owner schedule only'},sort_keys=True))
