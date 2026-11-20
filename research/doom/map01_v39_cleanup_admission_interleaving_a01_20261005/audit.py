#!/usr/bin/env python3
"""Independent raw-only audit; never imports or executes the candidate."""
import argparse, hashlib, json, subprocess
from pathlib import Path

PKG=Path(__file__).resolve().parent
PR_HEAD='39264f167f8f7541aaf10c43d287938b1317f520'
PR_FILES=[
 'research/doom/map01_v39_cancel_release_fix_a01_20261005/bridge_v2_candidate.py',
 'research/doom/map01_v39_cancel_release_fix_a01_20261005/input_owner_v13_candidate.py',
 'research/doom/map01_v39_cancel_release_fix_a01_20261005/test_cancel_release.py',
 'research/doom/map01_v39_perkey_bridge_a01/test_bridge.py',
 'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/input_owner_v12.py',
 'research/doom/map01_attack_onset_phase_allocation_02_v1/dependencies/v12/test_input_owner_v12.py',
]
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def read_json(name): return json.loads((PKG/name).read_text())
def check_cleanup_attempt(r, expected_head, expected_id, expected_step):
    assert r['candidate_invocations']==1
    assert r['candidate_head']==expected_head
    assert r['cleanup_completed_before_owner_call_return'] is True
    states=r['owner_state_samples_at_injected_boundary']
    assert states and states[0]['owned_keycodes']==[74]
    state=states[-1]
    assert state['owned_keycodes']==[] and state['owned_buttons']==[]
    assert r['poll_count']==len(states)
    assert len(r['owner_cleanup_records_before_return'])==1
    cleanup=r['owner_cleanup_records_before_return'][0]
    assert cleanup['event']=='owner_release' and cleanup['verified'] is True
    assert cleanup['keys_down']==[] and cleanup['buttons_down']==[]
    down=r['down_receipt']; ups=r['release_receipts']; assert len(ups)==1
    up=ups[0]; dm=down['physical_key_measurement']; um=up['physical_key_measurement']
    assert r['events']==['input_admission','input_release_measurement']
    assert (down['id'],down['step'],down['key'])==(up['id'],up['step'],up['key'])
    assert down['key']=='F8' and down['id']==expected_id and down['step']==expected_step
    assert down['intent_token']==up['intent_token']==dm['bracket']['intent_token']==um['bracket']['intent_token']
    assert down['owner_id']==up['owner_id']==dm['bracket']['owner_id']==um['bracket']['owner_id']
    assert dm['actuation_id']==um['actuation_id']
    cleanup_rows=cleanup['per_key_release_measurements']
    assert len(cleanup_rows)==1
    cleanup_row=cleanup_rows[0]
    assert (cleanup_row['event'],cleanup_row['id'],cleanup_row['step'],cleanup_row['key'])==('input_release_measurement',expected_id,expected_step,'F8')
    assert cleanup_row['physical_key_measurement']['actuation_id']==dm['actuation_id']
    assert um['classification']=='CONFIRMED_PHYSICAL_UP' and um['identity_status']=='RETIRED'
    assert um['adapter_edge']['edge']=='up' and um['adapter_edge']['status']=='CONFIRMED_PHYSICAL_UP'
    assert um['adapter_edge']['actuation_id']==dm['actuation_id']
    pre,post=um['pre_sample'],um['post_sample']
    assert pre['available'] is True and pre['down'] is True and pre['error'] is None
    assert post['available'] is True and post['down'] is False and post['error'] is None
    assert pre['finished_ns'] <= um['release_request_ns'] <= um['sync_return_ns'] <= post['started_ns']
    assert um['bracket']['physical_up_interval']==[pre['finished_ns'],post['finished_ns']]
    assert um['grants_input_authority'] is False and um['application_consumption_observed'] is False
    assert up['grants_input_authority'] is False
    assert up['reason']=='cancelled'
    assert r['fake_physical_keys_after_execute']==[] and r['bridge_held_after_execute']==[]

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--candidate-repo',type=Path,default=Path('/Users/taka/Documents/Codex/2026-10-03/new-chat-6/work/pr7805-admission-race-probe'))
    args=parser.parse_args()
    freeze=read_json('FREEZE.json'); lock=read_json('SOURCE_LOCK.json')
    a01=read_json('attempts/A01_INCONCLUSIVE_RAW.json')
    state=a01['owner_state_at_injected_boundary']
    assert a01['cleanup_completed_before_down_return'] is True  # probe's unsupported label
    assert state['owned_keycodes']==[74] and state['owned_buttons']==[]
    check_cleanup_attempt(read_json('attempts/A02_PASS_8414805493_RAW.json'), '84148054938965dc245602e37220586e07c6f28e', 'race-a02', 8)
    current=read_json('attempts/A03_PASS_39264f167f_RAW.json')
    check_cleanup_attempt(current, PR_HEAD, 'race-a03', 9)
    assert freeze['candidate_head']==PR_HEAD and freeze['classification']=='post-run provenance freeze'
    for rel,expected in freeze['artifact_sha256'].items():
        assert sha_bytes((PKG/rel).read_bytes())==expected, f'frozen package input changed: {rel}'
    assert PR_HEAD in lock['source_sets']
    assert '84148054938965dc245602e37220586e07c6f28e' in lock['source_sets']
    for head,blobs in lock['source_sets'].items():
        for rel,expected in blobs.items():
            b=subprocess.check_output(['git','-C',str(args.candidate_repo),'show',f'{head}:{rel}'])
            assert sha_bytes(b)==expected, f'source blob changed at {head}: {rel}'
    for attempt, expected in lock['runner_sha256'].items():
        assert sha_bytes((PKG/'attempts'/attempt).read_bytes())==expected, f'runner changed: {attempt}'
    result={'audit':'PASS_ADMISSION_RETURN_RACE_CONSTRUCTION','scope':'one fake-owner/fake-display scenario on the frozen PR #7805 candidate','attempts':{'A01':'HOLD: owner state still showed F8 down, so cleanup-before-return was unproved','A02':'PASS on superseded PR head 8414805493','A03':'PASS on current pinned PR head 39264f167f'},'verified':{'pre_return_empty_state_and_cleanup_record':True,'event_order':['input_admission','input_release_measurement'],'matching_actuation_and_context':True,'confirmed_sampled_up_bracket':True,'final_fake_display_and_bridge_state_empty':True},'limits':['No real OS input, X11, game, application effect, recovery benefit, or live Issue #59 allocation.']}
    (PKG/'AUDIT.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
if __name__=='__main__': main()
