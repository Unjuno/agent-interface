from __future__ import annotations
import copy, hashlib, importlib.util, json, platform, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
LIVE = HERE.parent
EVENTS = LIVE / 'results/expiry-observation-01/runtime/events.jsonl'
PROBE = LIVE / 'probe_expiry_observation_v1.py'
COLLECTOR = LIVE / 'post_release_observation_v2.py'
BRIDGE = LIVE / 'authority_ended_restart_durability_v1/authority_ended_bridge_v1.py'
EXPECTED_BLOBS = {
    EVENTS: 'aae6d81013e479d2ad1f2f068ccc4c8ad5c8c653',
    PROBE: '3c6e3ad67199ad530a1ae9ef64c34cd543022790',
    COLLECTOR: '83b7ebda20cc2aa499ca3e9f7ee18ce8bb291e07',
    BRIDGE: '9fcfdce5229cb58b3d1a17aacbcef0cb44bd10f1',
}

def git_blob_sha(path: Path) -> str:
    data = path.read_bytes()
    return hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest()

def verify_sources():
    result = {}
    for path, expected in EXPECTED_BLOBS.items():
        actual = git_blob_sha(path)
        if actual != expected:
            raise AssertionError(f'blob mismatch for {path}: {actual} != {expected}')
        result[str(path.relative_to(LIVE))] = {
            'git_blob_sha1': actual,
            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
        }
    return result

def load_bridge():
    spec = importlib.util.spec_from_file_location('frozen_authority_ended_bridge_v1', BRIDGE)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module

def reject(bridge, receipt):
    try:
        return {'accepted': True, 'decision': bridge.to_caller_execution_decision(receipt)}
    except bridge.AuthorityEndedNotReady as exc:
        return {'accepted': False, 'error': str(exc)}

def main():
    identities = verify_sources()
    events = [json.loads(line) for line in EVENTS.read_text(encoding='utf-8').splitlines()]
    terminal = next(e for e in events if e.get('event') == 'terminal' and e.get('id') == 'expire-hold')
    stopped = next(e for e in events if e.get('event') == 'input_stopped' and e.get('id') == 'expire-hold')
    accepted = next(e for e in events if e.get('event') == 'accepted' and e.get('id') == 'expire-hold')
    post_sequences = terminal['post_release_observation']['sequences']
    post_observations = [next(e for e in events if e.get('event') == 'observation' and e.get('id') == 'expire-hold' and e.get('sequence') == seq) for seq in post_sequences]
    first_post_index = min(events.index(e) for e in post_observations)
    terminal_index = events.index(terminal)
    stopped_index = events.index(stopped)
    last_pre_sequence = max(e['sequence'] for e in events[:first_post_index] if e.get('event') == 'observation' and e.get('id') == 'expire-hold')
    after_release_before_terminal = events[stopped_index + 1:terminal_index]
    after_stop_same_program = [e for e in events[stopped_index + 1:terminal_index + 1] if e.get('id') == 'expire-hold']
    post = terminal['post_release_observation']
    old_deadline = accepted['valid_until_ns']

    provenance = {
        'terminal_status': {'status':'CONTRADICTORY','value':terminal['status'],'required':'authority_ended','source':'terminal.status'},
        'release_verified': {'status':'DIRECT','value':terminal['release']['verified'],'required':True,'source':'terminal.release.verified'},
        'keys_down': {'status':'DIRECT','value':terminal['release']['keys_down'],'required':[],'source':'terminal.release.keys_down'},
        'buttons_down': {'status':'DIRECT','value':terminal['release']['buttons_down'],'required':[],'source':'terminal.release.buttons_down'},
        'post_release_input_admissions': {'status':'DERIVED','value':sum(e.get('event') == 'input_admission' for e in after_release_before_terminal),'required':0,'source':'count input_admission after input_stopped and before terminal'},
        'steps_completed': {'status':'DIRECT','value':terminal['steps_completed'],'required':'nonnegative int','source':'terminal.steps_completed'},
        'post_authority.grants_input_authority': {'status':'DERIVED','value':False,'required':False,'source':'terminal.post_release_observation.authority explicitly says no input or lease renewal'},
        'post_authority.tail_program_steps_resumed': {'status':'DERIVED','value':sum(e.get('event') in ('step_started','step_completed','input_admission') for e in after_stop_same_program),'required':0,'source':'no program-step/input events after input_stopped; stopped.followup says no further program steps'},
        'post_authority.captures': {'status':'CONTRADICTORY','value':post['captures'],'required':1,'source':'terminal.post_release_observation.captures'},
        'post_authority.sequence': {'status':'AMBIGUOUS','value':post_sequences,'required':'one positive int for exactly one capture','source':'legacy two-capture contract has no canonical single-capture selection rule'},
        'post_authority.sequence_advanced': {'status':'DERIVED','value':min(post_sequences) > last_pre_sequence,'required':True,'source':'minimum post-release sequence is greater than last pre-release sequence'},
        'post_authority.error': {'status':'DIRECT','value':post['error'],'required':None,'source':'terminal.post_release_observation.error'},
        'post_authority.within_lifecycle_deadline': {'status':'UNAVAILABLE','value':None,'required':True,'source':'no retained post-authority lifecycle-deadline assertion/field'},
        'post_authority.snapshot_finished_ns': {'status':'UNAVAILABLE','value':None,'required':'int','source':'legacy observations expose capture/image-ready/input-state sample times but no newer snapshot_finished_ns contract'},
        'post_authority.lifecycle_deadline_ns': {'status':'UNAVAILABLE','value':None,'required':'int','source':'only old command valid_until_ns exists and it expires before release/post-release capture'},
    }

    receipt = {
        'terminal_status': terminal['status'],
        'release_verified': terminal['release']['verified'],
        'keys_down': terminal['release']['keys_down'],
        'buttons_down': terminal['release']['buttons_down'],
        'post_release_input_admissions': provenance['post_release_input_admissions']['value'],
        'steps_completed': terminal['steps_completed'],
        'post_authority': {
            'grants_input_authority': False,
            'tail_program_steps_resumed': provenance['post_authority.tail_program_steps_resumed']['value'],
            'captures': post['captures'],
            'sequence_advanced': provenance['post_authority.sequence_advanced']['value'],
            'error': post['error'],
        },
    }
    bridge = load_bridge()
    first = reject(bridge, receipt)
    relabel = copy.deepcopy(receipt); relabel['terminal_status'] = 'authority_ended'
    relabel_result = reject(bridge, relabel)
    collapse = copy.deepcopy(relabel); collapse['post_authority']['captures'] = 1; collapse['post_authority']['sequence'] = post_sequences[-1]
    collapse_result = reject(bridge, collapse)

    timing = {
        'old_command_valid_until_ns': old_deadline,
        'release_verified_ns': terminal['release']['verified_ns'],
        'release_minus_old_deadline_ns': terminal['release']['verified_ns'] - old_deadline,
        'first_post_capture_ns': post_observations[0]['capture_ns'],
        'first_capture_minus_old_deadline_ns': post_observations[0]['capture_ns'] - old_deadline,
        'first_image_ready_ns': post_observations[0]['image_ready_ns'],
        'first_image_ready_minus_old_deadline_ns': post_observations[0]['image_ready_ns'] - old_deadline,
        'second_post_capture_ns': post_observations[1]['capture_ns'],
        'second_capture_minus_old_deadline_ns': post_observations[1]['capture_ns'] - old_deadline,
        'old_deadline_reusable_for_post_authority': False,
    }
    bad = [key for key, value in provenance.items() if value['status'] in ('CONTRADICTORY','AMBIGUOUS','UNAVAILABLE')]
    hard_gate = (
        first == {'accepted':False,'error':'scheduled authority_ended status required'} and
        relabel_result == {'accepted':False,'error':'exactly one passive post-authority capture required'} and
        collapse_result == {'accepted':False,'error':'post-authority observation outside lifecycle deadline'} and
        timing['release_minus_old_deadline_ns'] > 0 and timing['first_capture_minus_old_deadline_ns'] > 0 and
        {'terminal_status','post_authority.captures','post_authority.within_lifecycle_deadline','post_authority.snapshot_finished_ns','post_authority.lifecycle_deadline_ns'}.issubset(bad)
    )
    result = {
        'schema':'inkscape-expired-authority-semantics-v1-result',
        'base_commit':'0bf4103e69e4108f92a153e38a5ea1f7253f1f93',
        'source_identities':identities,
        'provenance':provenance,
        'unsupported_or_contradictory_fields':bad,
        'evidence_only_receipt':receipt,
        'unchanged_bridge_first_result':first,
        'diagnostic_counterfactual_relabel_only':relabel_result,
        'diagnostic_counterfactual_relabel_and_single_capture':collapse_result,
        'timing':timing,
        'hard_gate_pass':hard_gate,
        'decision':'FAIL_DIRECT_UPGRADE_RETAIN_SEMANTIC_MISMATCH' if hard_gate else 'RETAIN_AUDIT_FAILURE',
        'environment':{'python':sys.version.split()[0],'platform':platform.platform()},
        'limits':['retained artifact/source audit only','no live GUI','no model','no OS input','no network side effects'],
    }
    print(json.dumps(result, indent=2, sort_keys=True))

if __name__ == '__main__':
    main()
