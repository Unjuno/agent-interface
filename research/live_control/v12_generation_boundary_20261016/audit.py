"""Saved Fake X record checker; never imports or executes the input owner."""
import hashlib
import json
from pathlib import Path


def audit(raw):
    def require(condition, label):
        if not condition:
            raise ValueError(label)
    rows = raw['rows']
    require([row['case'] for row in rows] == ['stable', 'same_xid_new_pid',
            'same_xid_pid_new_start', 'changed_focus'], 'exact four cells')
    stale = 0
    for row in rows:
        expected, current = row['source_generation'], row['fixture_current_generation']
        eligible = expected == current and row['fixture_focus'] == expected['xid']
        require(row['reference_eligible'] is eligible, 'reference predicate')
        presses = [event for event in row['events'] if event['kind'] == 2]
        releases = [event for event in row['events'] if event['kind'] == 3]
        admitted = row['admission'] is not None
        require(admitted == bool(presses), 'admission/emission association')
        if row['case'] == 'changed_focus':
            require(not admitted and row['error_type'] == 'DecisionRequired' and
                    not row['events'] and row['held_after_admission_call'] == [], 'focus refusal control')
        else:
            require(admitted and row['error_type'] is None and
                    row['admission']['event'] == 'input_admission' and
                    presses == [{'kind': 2, 'code': 38}] and
                    releases == [{'kind': 3, 'code': 38}] and
                    row['held_after_admission_call'] == [38], 'one press and one cleanup release')
            stale += int(not eligible)
        require(row['release']['verified'] is True and
                row['release']['keys_down'] == [] and row['release']['buttons_down'] == [] and
                row['final_fake_keys'] == [] and row['owner_thread_stopped'] is True, 'fake cleanup and thread exit')
    require(stale == 2, 'two observed metadata-ignored admissions')
    require(raw['task_success_verified'] is False, 'no task claim')
    return {'disposition': 'REPRODUCED_METADATA_IGNORED_AT_CURRENT_V4_V12_OWNER',
            'generation_contract_satisfied': False, 'stale_admissions': stale,
            'fresh_control_admitted': True, 'changed_focus_control_refused': True,
            'fake_cleanup_verified': True, 'owner_threads_stopped': True,
            'scope': 'owner boundary with probe-supplied metadata; not a live XID-reuse or standard observation-to-lease integration test'}


if __name__ == '__main__':
    directory = Path(__file__).resolve().parent
    root = directory.parents[2]
    raw = json.loads((directory / 'first-outcome.json').read_text())
    freeze = json.loads((directory / 'FREEZE.json').read_text())
    if raw['freeze'] != freeze:
        raise ValueError('freeze association')
    for path, digest in freeze['source_sha256'].items():
        if hashlib.sha256((root / path).read_bytes()).hexdigest() != digest:
            raise ValueError('source bytes changed: ' + path)
    print(json.dumps(audit(raw), indent=2))
