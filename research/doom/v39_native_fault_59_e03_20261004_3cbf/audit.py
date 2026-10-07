"""Independent saved-only native evidence checks; never invokes producer/game."""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile

EXPECTED = {'original_fault': ('TimeoutError', None, False),
            'candidate_fault': ('_SessionReaderFailure', 'JSONDecodeError', False),
            'candidate_healthy': ('TimeoutError', None, True)}


def semantic_check(row, events):
    try:
        identifier = row['id']; token = row['expected_token']
        if not isinstance(token, str) or not token:
            return False
        selected = []
        for field, event in [('accepted', 'accepted'), ('cancel', 'cancel_requested'),
                             ('released', 'input_released'), ('terminal', 'terminal')]:
            found = [(index, r) for index, r in enumerate(events)
                     if r.get('event') == event and r.get('id') == identifier]
            if len(found) != 1 or json.dumps(found[0][1], sort_keys=True) != json.dumps(row[field], sort_keys=True):
                return False
            selected.append(found[0])
        positions = [index for index, r in selected]
        clocks = [r['emit_ns'] for index, r in selected]
        if positions != sorted(set(positions)) or clocks != sorted(set(clocks)):
            return False
        if row['accepted']['intent_token'] != token or row['released']['intent_token'] != token:
            return False
        if row['cancel']['matched'] is not True or row['terminal']['status'] != 'cancelled':
            return False
        interruption = row['terminal']['interruption']
        if interruption['intent_token'] != token or json.dumps(interruption['record'], sort_keys=True) != json.dumps(row['released']['owner_release'], sort_keys=True):
            return False
        if interruption['record']['reason'] != 'cancelled':
            return False
        for evidence in (row['released']['owner_release'], row['terminal']['release']):
            if evidence['verified'] is not True or evidence['keys_down'] != [] or evidence['buttons_down'] != []:
                return False
        if row['before'] != {'keys': [], 'buttons': []} or row['after'] != {'keys': [], 'buttons': []}:
            return False
        if type(row['right_code']) is not int or not 8 <= row['right_code'] <= 255:
            return False
        if row['held'] != {'keys': [row['right_code']], 'buttons': []}:
            return False
        return (type(row['child_exit']) is int and row['child_exit'] == 0
                and row['after_ns'] > clocks[-1] and row['cleanup_faults'] == [] and row['fatal'] is None)
    except (KeyError, TypeError):
        return False


def audit(root, record):
    with tarfile.open(root / 'source-closure.tar.gz', 'r:gz') as archive:
        source = {m.name: hashlib.sha256(archive.extractfile(m).read()).hexdigest()
                  for m in archive.getmembers() if m.isfile()}
    runtime = json.loads((record / 'RUNTIME.json').read_text())
    assert runtime['uid'] == 501 and runtime['limits'] == {
        'cpu.max': '100000 100000', 'memory.max': '1073741824', 'memory.swap.max': '0', 'pids.max': '128'}
    summary = json.loads((record / 'SUMMARY.json').read_text())
    assert summary['formal_runs'] == 1 and summary['retries'] == 0 and summary['model_calls'] == 0
    cases = summary['cases']
    assert cases == list(EXPECTED)[:len(cases)] and 1 <= len(cases) <= 3
    outcomes = []
    for case in cases:
        cell = record / case
        row = json.loads((cell / 'RESULT.json').read_text())
        events = [json.loads(line) for line in (cell / 'native-stdout.jsonl').read_text().splitlines()]
        imported = json.loads((cell / 'imports.json').read_text())
        assert imported['backend_module'] == 'doom_typed_release_backend_v1'
        assert imported['loaded']
        for item in imported['loaded']:
            assert source[item['path']] == item['sha256']
        assert imported['session_sha256'] == source['research/doom/session_map01_v12.py']
        matches = semantic_check(row, events)
        assert matches == row['release_gate']
        outcome_ok = False
        if matches:
            wanted, cause, alive = EXPECTED[case]
            outcome_ok = (row['wait_outcome'] == wanted and row['cause'] == cause
                          and row['reader_alive_at_cancel'] is alive)
            expected_hold = {'keys': [row['right_code']], 'buttons': []}
            outcome_ok = outcome_ok and row['after_notification'] == expected_hold and row['before_cancel'] == expected_hold
            assert outcome_ok == row['outcome_gate']
            snapshot = 'v39-original.py.txt' if case == 'original_fault' else 'v39-candidate.py.txt'
            assert row['reader_sha256'] == source['research/doom/v39_reader_signal_59_e02_20261004_3cbf/source/' + snapshot]
            assert row['held_ns'] < row['wait_start_ns'] <= row['wait_end_ns'] < row['cancel_send']['start_ns']
            assert row['wait_end_ns'] <= row['notification_sample_ns'] <= row['before_cancel_ns'] < row['cancel_send']['start_ns']
            if case == 'candidate_healthy':
                assert row['injected_ns'] is None and row['injection_state'] is None and row['unhandled'] == []
            else:
                assert row['injection_state'] == expected_hold
                assert row['held_ns'] < row['fault_requested_ns'] <= row['injected_ns'] <= row['wait_end_ns']
                assert row['injected_ns'] < row['cancel_send']['start_ns']
                if case == 'original_fault':
                    assert len(row['unhandled']) == 1 and row['unhandled'][0]['thread'] == 'selected-v39-reader'
                    assert row['unhandled'][0]['type'] == 'JSONDecodeError'
                else:
                    assert row['unhandled'] == []
        outcomes.append(matches and outcome_ok)
    primary = len(outcomes) == 3 and all(outcomes)
    assert summary['verdict'] == ('PASS_SCOPED_NATIVE_FAULT_CANCEL_RELEASE' if primary else 'STOP_NATIVE_GATE')
    assert all(outcomes[:-1])
    hashes = {str(p.relative_to(record)): hashlib.sha256(p.read_bytes()).hexdigest()
              for p in sorted(record.rglob('*')) if p.is_file()}
    return {'audit': 'PASS_SAVED_NATIVE_CUSTODY', 'native_verdict': summary['verdict'],
            'cases': cases, 'source_files': len(source), 'payload_sha256': hashes,
            'producer_reruns': 0, 'scope': 'saved evidence validity; not independent live repetition'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args(); result = audit(args.root, args.record)
    args.out.write_text(json.dumps(result, sort_keys=True) + '\n')
    print(result['audit'], result['native_verdict'])
