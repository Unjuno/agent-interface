"""Audit saved CLI output only. No imports of runtime, runner, or test fixtures."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from io_data import inputs

HERE = Path(__file__).resolve().parent


def audit(record, cases, freeze, *, full=True):
    errors = []
    checks = 0
    def check(ok, label):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(label)
    expected_keys = {(c['id'], route, mode) for c in cases
                     for route in ('file', 'stdin') for mode in range(3)}
    rows = record['rows']
    keys = [(r['case'], r['route'], r['mode']) for r in rows]
    expected_count = 180 if full else len(cases) * 6
    check(len(rows) == expected_count and record['count'] == expected_count, 'denominator')
    check(len(cases) == (30 if full else 3), 'input_denominator')
    check(len(set(keys)) == len(keys) and set(keys) == expected_keys, 'row_identity')
    check(record['source_before'] == freeze == record['source_after'], 'frozen_sources')
    check(record['started_ns'] <= record['ended_ns'], 'matrix_order')
    by_id = {c['id']: c for c in cases}
    statuses = Counter()
    schemas = Counter()
    for row in rows:
        label = f"{row['case']}/{row['route']}/{row['mode']}"
        c = by_id[row['case']]
        raw = c['raw'].encode('utf-8')
        original = json.loads(raw)
        result = original['result']
        ex = result.get('execution', {})
        check(hashlib.sha256(raw).hexdigest() == c['sha256'] == row['input_sha256'], label + ':input_identity')
        check(row['input_unchanged'] is True, label + ':input_changed')
        check(row['directory_files'] == ['report.json'], label + ':unexpected_files')
        check(row['stdin'] == (c['raw'] if row['route'] == 'stdin' else ''), label + ':stdin')
        check(row['pid'] > 0 and record['started_ns'] <= row['started_ns'] <= row['ended_ns'] <= record['ended_ns'], label + ':process_order')
        args = row['argv']
        flags = [[], ['--compact'], ['--compact', '--report-refs']][row['mode']]
        report_path = str(Path(row['cwd']) / 'report.json')
        check(args[1:] == ['-S', '-B', '-m', 'runtime.cli_v1', 'review', '--report',
              report_path if row['route'] == 'file' else '-', '--run-directory', row['cwd'], *flags], label + ':command')
        image_missing = c['id'] == 'image_missing'
        check(row['exit'] == (2 if image_missing else 0), label + ':exit')
        check(row['stderr'] == '', label + ':stderr')
        output = json.loads(row['stdout'])
        view = output['receipt']
        source = view['source']
        summary = output['outcome_summary']
        check(output['authority'] == view['authority'] == 'none', label + ':authority')
        check('task_success' not in summary, label + ':invented_task_success')
        check(output['image'] is None, label + ':invented_image')
        check(output['image_status'] == ('needs_review' if image_missing else 'no_observation'), label + ':image_status')
        check(source['sha256'] == c['sha256'] and source['bytes'] == len(raw), label + ':source_digest')
        check(source['path'] == (report_path if row['route'] == 'file' else None), label + ':source_path')
        check(view['schema'] in ('agent-interface/receipt-view-v1', 'agent-interface/receipt-view-v3-report-ref'), label + ':view_schema')
        if view['schema'].endswith('v3-report-ref'):
            check(row['mode'] == 2 and row['route'] == 'stdin', label + ':ref_mode')
            check(view['report_reference'] == '/source/raw_report' and view['report'] == {'report_ref': '/source/raw_report'}, label + ':ref_binding')
            restored = source['raw_report']
        else:
            restored = view['report']
        check(json.dumps(restored, sort_keys=True) == json.dumps(original, sort_keys=True), label + ':raw_preservation')
        if row['route'] == 'stdin':
            check(source['kind'] == 'received_bytes' and source['raw_report'] == original, label + ':stdin_history')
        statuses[result['status']] += 1
        schemas[view['schema']] += 1
        check(summary['reported_status'] == original['status'], label + ':reported_status')
        check(summary['execution_status'] == result['status'], label + ':execution_status')
        check(summary['execution_error'] == result.get('error'), label + ':execution_error')
        check(summary['execution_detail'] == result.get('detail'), label + ':execution_detail')
        check(summary['failure_detail'] == ex.get('error'), label + ':failure_detail')
        check(summary['failed_operation_effect'] == ex.get('failed_op_effect'), label + ':partial_uncertainty')
        check(summary['recovery_required'] == result.get('recovery_required'), label + ':recovery')
        is_static = result.get('error') == 'INVALID_PROGRAM'
        is_partial = result['status'] == 'execution_failed'
        failed = 13 if is_partial and c['id'] != 'failed_boolean' else None
        invalid = 13 if is_static else None
        check(summary['validation_operation_index'] == invalid, label + ':validation_index')
        check(summary['failed_operation_index'] == failed, label + ':failure_index')
        if 'compilation' in original:
            mapping = {'source_operation_index': 4, 'expanded_occurrence': 1}
            expected_validation = mapping if is_static and not c['id'].startswith('map_') else None
            expected_failure = mapping if failed is not None else None
            check(summary['validation_source_operation'] == expected_validation, label + ':validation_source')
            check(summary['failed_source_operation'] == expected_failure, label + ':failure_source')
        else:
            check('failed_source_operation' not in summary and 'validation_source_operation' not in summary, label + ':invented_compilation')
        # These finite inputs have only missing, complete neutral, or explicit failed release.
        if c['id'] == 'release_failed_then_success':
            release = False
        elif c['id'] == 'release_missing' or result.get('error') in ('INVALID_PROGRAM', 'STALE_BINDING'):
            release = None
        else:
            release = True
        check(summary['input_release_verified'] is release, label + ':release')
    return {'status': 'PASS_REVIEW_COMPILATION_FIDELITY' if not errors else 'HOLD_OR_FAIL_REVIEW_FIDELITY',
            'checks': checks, 'errors': errors, 'records': len(rows),
            'historical_execution_statuses_presented': dict(sorted(statuses.items())),
            'view_schemas': dict(sorted(schemas.items())), 'new_gui_runs': 0,
            'new_task_success_claims': 0, 'external_review': False}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('records', type=Path)
    args = p.parse_args()
    result = audit(json.loads(args.records.read_text()), inputs(HERE),
                   json.loads((HERE / 'FREEZE.json').read_text())['files'])
    print(json.dumps(result, sort_keys=True, indent=2))
    return int(bool(result['errors']))


if __name__ == '__main__':
    raise SystemExit(main())
