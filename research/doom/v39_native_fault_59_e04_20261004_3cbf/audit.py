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
        if any(type(clock) is not int or clock <= 0 for clock in clocks):
            return False
        if type(row['after_ns']) is not int or row['after_ns'] <= 0:
            return False
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


def require(condition, reason):
    if not condition:
        raise ValueError(reason)


def equal(left, right):
    return json.dumps(left, sort_keys=True) == json.dumps(right, sort_keys=True)


def audit(root, record, native_inspect=None, export=None):
    from partial_stop import classify_partial_stop
    freeze = json.loads((root / 'FREEZE.json').read_text())
    archive_path = root / 'source-closure.tar.gz'
    require(hashlib.sha256(archive_path.read_bytes()).hexdigest() == freeze['source_archive_sha256'], 'archive identity')
    with tarfile.open(archive_path, 'r:gz') as archive:
        members = [m for m in archive.getmembers() if m.isfile()]
        source = {m.name: hashlib.sha256(archive.extractfile(m).read()).hexdigest() for m in members}
        require(len(source) == len(members), 'duplicate archive member')
    pinned_source = {}
    for line in (root / 'SOURCE_PINS.sha256').read_text().splitlines():
        digest, name = line.split('  ', 1)
        require(name not in pinned_source, 'duplicate source pin')
        pinned_source[name] = digest
    require(source == pinned_source and bool(source), 'source archive/pin closure')
    execution = {}
    for line in (root / 'EXECUTION_PINS.sha256').read_text().splitlines():
        digest, relative = line.split('  ', 1)
        path = (root / relative).resolve()
        require(path.is_relative_to(root.resolve()) and relative not in execution, 'execution path/collision')
        require(hashlib.sha256(path.read_bytes()).hexdigest() == digest, 'execution hash')
        execution[relative] = digest
    closure = {'runner.py', 'gate.py', 'audit.py', 'session_entry.py',
               'PROTOCOL.md', 'FREEZE.json', 'SOURCE_PINS.sha256',
               'source-closure.tar.gz', 'COMMANDS.md'}
    # Read-only predecessor compatibility is explicit, not an E04 launch mode.
    if freeze['allocation'] != 'v39-native-fault-e03-3cbf-20261004':
        closure.add('partial_stop.py')
    require(set(execution) == closure, 'execution closure')
    runtime = json.loads((record / 'RUNTIME.json').read_text())
    require(type(runtime['uid']) is int and runtime['uid'] == 501, 'native UID')
    require(equal(runtime['limits'], {'cpu.max': '100000 100000', 'memory.max': '1073741824', 'memory.swap.max': '0', 'pids.max': '128'}), 'native cgroup sample')
    require(equal(runtime['freeze'], freeze), 'runtime/freeze')
    require(type(runtime['source_pins']) is int and runtime['source_pins'] == len(source), 'source count')
    require(type(runtime['execution_pins']) is int and runtime['execution_pins'] == len(execution), 'execution count')
    summary = json.loads((record / 'SUMMARY.json').read_text())
    for field, wanted in [('formal_runs', 1), ('retries', 0), ('model_calls', 0)]:
        require(type(summary[field]) is int and summary[field] == wanted, 'summary count')
    require(summary['gameplay_success_claim'] is False, 'unsupported gameplay claim')
    cases = summary['cases']
    require(type(cases) is list and cases == list(EXPECTED)[:len(cases)] and 1 <= len(cases) <= 3, 'case prefix')
    require(type(summary['cells']) is int and summary['cells'] == len(cases), 'cell count')
    require({p.name for p in record.iterdir() if p.is_dir()} == set(cases), 'saved cell set')
    require(freeze['cases'] == list(EXPECTED), 'frozen case order')
    outcomes = []; dispositions = []
    for index, case in enumerate(cases):
        require(not outcomes or outcomes[-1], 'later cell after STOP')
        cell = record / case
        row = json.loads((cell / 'RESULT.json').read_text())
        require(row['case'] == case, 'result case')
        raw = (cell / 'native-stdout.jsonl').read_bytes()
        snapshot = 'v39-original.py.txt' if case == 'original_fault' else 'v39-candidate.py.txt'
        require(row['reader_sha256'] == source['research/doom/v39_reader_signal_59_e02_20261004_3cbf/source/' + snapshot], 'reader source')
        imports = cell / 'imports.json'
        if not imports.exists():
            partial = classify_partial_stop(row, raw, (cell / 'session.stderr.log').read_bytes(), False)
            require(index == len(cases) - 1, 'later cell after partial STOP')
            outcomes.append(False); dispositions.append(partial['saved_disposition'])
            continue
        events = [json.loads(line) for line in raw.decode('utf-8').splitlines()]
        imported = json.loads(imports.read_text())
        require(imported['backend_module'] == 'doom_typed_release_backend_v1' and bool(imported['loaded']), 'backend imports')
        for item in imported['loaded']:
            require(source[item['path']] == item['sha256'], 'loaded source')
        require(imported['session_sha256'] == source['research/doom/session_map01_v12.py'], 'session source')
        matches = semantic_check(row, events)
        require(row['release_gate'] is matches, 'release gate')
        outcome_ok = False
        if matches:
            wanted, cause, alive = EXPECTED[case]
            outcome_ok = row['wait_outcome'] == wanted and row['cause'] == cause and row['reader_alive_at_cancel'] is alive
            held = {'keys': [row['right_code']], 'buttons': []}
            outcome_ok = outcome_ok and equal(row['after_notification'], held) and equal(row['before_cancel'], held)
            for field in ('held_ns', 'wait_start_ns', 'wait_end_ns', 'notification_sample_ns', 'before_cancel_ns'):
                require(type(row[field]) is int and row[field] > 0, 'exposure clock')
            require(row['held_ns'] < row['wait_start_ns'] <= row['wait_end_ns'] < row['cancel_send']['start_ns'], 'wait/cancel order')
            require(row['wait_end_ns'] <= row['notification_sample_ns'] <= row['before_cancel_ns'] < row['cancel_send']['start_ns'], 'notification hold order')
            if case == 'candidate_healthy':
                require(row['injected_ns'] is None and row['injection_state'] is None and row['unhandled'] == [], 'healthy no injection')
            else:
                require(equal(row['injection_state'], held), 'injection hold')
                require(row['held_ns'] < row['fault_requested_ns'] <= row['injected_ns'] <= row['wait_end_ns'] < row['cancel_send']['start_ns'], 'fault order')
                if case == 'original_fault':
                    require(len(row['unhandled']) == 1 and row['unhandled'][0]['thread'] == 'selected-v39-reader' and row['unhandled'][0]['type'] == 'JSONDecodeError', 'original exception')
                else:
                    require(row['unhandled'] == [], 'candidate handled exception')
        require(row['outcome_gate'] is outcome_ok, 'outcome gate')
        outcomes.append(matches and outcome_ok)
        dispositions.append('VERIFIED_EXPOSED_CELL_PASS' if outcomes[-1]
                            else 'VERIFIED_IMPORTED_CELL_STOP_EXPOSURE_UNESTABLISHED')
    primary = len(outcomes) == 3 and all(outcomes)
    require(summary['verdict'] == ('PASS_SCOPED_NATIVE_FAULT_CANCEL_RELEASE' if primary else 'STOP_NATIVE_GATE'), 'summary disposition')
    receipt_path = native_inspect if native_inspect is not None else root / 'raw/native-container-inspect.json'
    receipt = json.loads(receipt_path.read_text())
    require(len(receipt) == 1, 'terminal receipt count')
    state = receipt[0]['State']
    require(state['Running'] is False and type(state['Pid']) is int and state['Pid'] == 0 and state['OOMKilled'] is False
            and type(state['ExitCode']) is int and state['ExitCode'] == (0 if primary else 1), 'native terminal')
    require(receipt[0]['Config']['Image'] == freeze['image'], 'native image')
    hashes = {str(p.relative_to(record)): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(record.rglob('*')) if p.is_file()}
    export = export if export is not None else root / 'raw/export'
    require(export.resolve() != record.resolve() and export.is_dir(), 'independent export path')
    exported = {str(p.relative_to(export)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sorted(export.rglob('*')) if p.is_file()}
    require(hashes == exported, 'independent export equality')
    return {'audit': 'VERIFIED_SAVED_NATIVE_RECORD', 'native_verdict': summary['verdict'], 'scientific_pass': primary,
            'cell_dispositions': dispositions, 'cases': cases, 'source_files': len(source), 'payload_sha256': hashes,
            'producer_reruns': 0, 'scope': 'saved record verification; no independent live repetition'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--record', type=Path, required=True); parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--native-inspect', type=Path)
    parser.add_argument('--export', type=Path)
    args = parser.parse_args(); result = audit(args.root, args.record, args.native_inspect, args.export)
    args.out.write_text(json.dumps(result, sort_keys=True) + '\n')
    print(result['audit'], result['native_verdict'])
