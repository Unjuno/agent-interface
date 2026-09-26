"""Independent raw-record checker. Does not import runtime or measurement code."""
import hashlib
import json
from pathlib import Path
import sys


def check(cases, arms, execution):
    errors = []
    def need(condition, reason):
        if not condition:
            errors.append(reason)
    need(len(cases) == 123 and len({x['id'] for x in cases}) == 123, 'cases')
    need(len(execution) == 2, 'worker_count')
    expected_ids = [x['id'] for x in cases]
    stats = {}
    for arm in ('baseline', 'candidate'):
        rows = arms[arm]
        need([r['id'] for r in rows] == expected_ids, arm + ':coverage')
        receipts = [r for r in execution if r['arm'] == arm]
        need(len(receipts) == 1, arm + ':receipt')
        if len(receipts) == 1:
            e = receipts[0]
            need(type(e['exit']) is int and e['exit'] == 0 and e['timeout'] is False, arm + ':exit')
            need(not e['stderr'], arm + ':stderr')
            need(json.loads(e['stdout'])['imported_native'] == [], arm + ':native_import')
        counts = {'valid': 0, 'invalid': 0, 'type_errors': 0, 'located_invalid': 0}
        for c, r in zip(cases, rows):
            key = arm + ':' + c['id']
            p = json.loads(c['input'])
            source_index = 0 if c['mode'] == 'plain' else 1
            expanded_index = {'plain': 0, 'repeat': 2, 'gap': 5}[c['mode']]
            op = p['ops'][source_index]
            kind = op['op']
            value = op.get('button' if kind == 'pointer_button' else 'frame')
            tokens = ['left','middle','right','x1','x2'] if kind == 'pointer_button' else ['screen_physical_px','screen_logical','window_client']
            valid = type(value) is str and value in tokens
            unhashable = type(value) in (list, dict)
            detail = {'observe':'invalid observe frame','pointer_move':'invalid pointer frame','pointer_button':'invalid pointer button'}[kind]
            need(r['input_sha256'] == hashlib.sha256(c['input'].encode()).hexdigest(), key + ':input_hash')
            need(r['input_unchanged'] is True and r['expanded_unchanged'] is True, key + ':mutation')
            cli = r['cli']
            need(type(cli['exit']) is int and cli['exit'] == (0 if valid else 1), key + ':cli_exit')
            need(cli['timeout'] is False and cli['stderr'] == '', key + ':cli_process')
            need(type(cli['pid']) is int and cli['pid'] > 0, key + ':pid')
            need(type(cli['start_ns']) is int and type(cli['end_ns']) is int and cli['end_ns'] >= cli['start_ns'], key + ':clock')
            report = r['static']
            need(json.loads(cli['stdout']) == dict(report, input_sha256=r['input_sha256']), key + ':cli_parity')
            need(report['static_valid'] is valid, key + ':static_verdict')
            need(report['side_effect_authority'] is False and report['task_success'] is None and
                 report['backend_checked'] is False and report['runtime_admission'] == 'not_evaluated', key + ':authority')
            if valid:
                counts['valid'] += 1
                need(r['core']['kind'] == 'valid' and r['admission']['accepted'] is True, key + ':valid')
                expected_caps = {'input.release_all', 'display.geometry'}
                expected_caps.add('capture.frame' if kind == 'observe' else 'input.pointer')
                if c['mode'] == 'repeat': expected_caps.add('input.keyboard')
                if c['mode'] == 'gap': expected_caps.update(('input.text', 'event.feedback', 'clock.monotonic'))
                need(report['required_capabilities'] == r['core']['caps'] == r['admission']['required_capabilities'] == sorted(expected_caps), key + ':caps')
                need(type(report['expanded_operation_count']) is int and report['expanded_operation_count'] == expanded_index + 2, key + ':expanded_count')
                need(report['source_operation_count'] == source_index + 2, key + ':source_count')
            else:
                counts['invalid'] += 1
                need(report['error'] == 'INVALID_PROGRAM', key + ':invalid')
                need('sentinel-k8r3' not in json.dumps(report), key + ':echo')
                if arm == 'baseline' and unhashable:
                    counts['type_errors'] += 1
                    need(r['core']['kind'] == 'TypeError' and r['core']['index'] is None and
                         r['admission'].get('exception') == 'TypeError', key + ':baseline_gap')
                    need('source_operation_index' not in report and 'expanded_operation_index' not in report, key + ':baseline_location')
                else:
                    counts['located_invalid'] += 1
                    need(r['core']['kind'] == 'ContractError' and type(r['core']['index']) is int and r['core']['index'] == expanded_index and
                         r['core']['detail'] == detail, key + ':core_location')
                    need(r['admission']['accepted'] is False and r['admission']['error'] == 'INVALID_PROGRAM' and r['admission']['required_capabilities'] == [], key + ':typed_refusal')
                    need(report.get('source_operation_index') == source_index and
                         type(report.get('source_operation_index')) is int and
                         report.get('expanded_operation_index') == expanded_index and
                         type(report.get('expanded_operation_index')) is int and report['detail'] == detail, key + ':static_location')
        stats[arm] = counts
    for b, c in zip(arms['baseline'], arms['candidate']):
        if b['core']['kind'] != 'TypeError':
            need(b['core'] == c['core'] and b['admission'] == c['admission'] and b['static'] == c['static'], b['id'] + ':unchanged_parity')
    return {'status': 'PASS_ENUM_CONTRACT_ENGINEERING' if not errors else 'FAIL_ENUM_CONTRACT_ENGINEERING',
            'errors': errors, 'counts': stats}


def load(path):
    cases = json.loads(Path(__file__).with_name('cases.json').read_text())
    arms = {a: [json.loads(line) for line in (path/a/'rows.jsonl').read_text().splitlines()]
            for a in ('baseline', 'candidate')}
    return cases, arms, json.loads((path/'EXECUTION.json').read_text())


if __name__ == '__main__':
    result = check(*load(Path(sys.argv[1])))
    print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(bool(result['errors']))
