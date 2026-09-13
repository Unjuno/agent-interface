"""Bind an offline report index to its exact clock/submit evidence; no authority."""
import argparse
import json
from pathlib import Path
from decision_receipt_v1 import build as index
from pointer_exchange_v1 import prefix, own_command
from report_pages_v2 import MAX_SOURCE


def exact(a, b):
    return json.dumps(a, sort_keys=True, allow_nan=False) == json.dumps(b, sort_keys=True, allow_nan=False)


def binding(report):
    exchanges = report['exchanges']
    if report.get('state') != 'terminal' or report.get('program_sent') is not True or report.get('reason'):
        raise ValueError('caller does not report a resolved attempted program')
    if len(exchanges) != 2:
        raise ValueError('expected one clock and one submit exchange')
    clock, submit = exchanges
    cq, sq = clock['request'], submit['request']
    if cq['command'] != {'op': 'clock'} or sq['command'].get('op') != 'submit':
        raise ValueError('clock/submit request pair required')
    if not all(isinstance(q.get('request_id'), str) and q['request_id'] for q in (cq, sq)) or cq['request_id'] == sq['request_id']:
        raise ValueError('distinct request identities required')
    cr = prefix(clock['reply'], cq['after'])
    ci = own_command(cr, cq['request_id'], 'clock')
    if ci != len(cr) - 2 or cr[-1].get('event') != 'clock':
        raise ValueError('own clock boundary required')
    if any(e.get('event') == 'command' for e in cr[:ci]):
        raise ValueError('historical/interleaved commands require review')
    now = cr[-1]
    source = report['source_image']
    if source.get('status') != 'image' or type(now.get('sequence')) is not int or now['sequence'] != source.get('sequence'):
        raise ValueError('clock/source sequence mismatch')
    if type(now.get('runtime_ns')) is not int or now['runtime_ns'] <= 0:
        raise ValueError('invalid clock time')
    if sq['after'] != clock['reply']['cursor']:
        raise ValueError('submit cursor does not follow clock')
    command = sq['command']
    if command.get('expected_sequence') != now['sequence']:
        raise ValueError('submit sequence mismatch')
    if type(command.get('valid_until_ns')) is not int or command['valid_until_ns'] <= now['runtime_ns']:
        raise ValueError('invalid reported lease deadline')
    records = prefix(submit['reply'], sq['after'])
    position = own_command(records, sq['request_id'], 'submit')
    if position != 0 or any(e.get('event') == 'command' for e in records[1:]):
        raise ValueError('unexpected command in submit evidence')
    echoed = dict(records[0]['command'])
    echoed.pop('transport_request_id')
    if not exact(echoed, command):
        raise ValueError('echoed command differs from submitted command')
    identifier = command.get('id')
    if not isinstance(identifier, str) or not identifier or sq.get('action_id') != identifier:
        raise ValueError('action identity mismatch')
    admissions = [r for r in records if r.get('event') == 'accepted']
    terminals = [r for r in records if r.get('event') == 'terminal']
    if len(admissions) != 1 or admissions[0].get('id') != identifier or len(terminals) != 1 or records[-1] != terminals[0] or terminals[0].get('id') != identifier:
        raise ValueError('unique own admission and final terminal required')
    if not isinstance(command.get('steps'), list) or not command['steps'] or admissions[0].get('steps') != len(command['steps']):
        raise ValueError('admitted step count mismatch')
    if admissions[0].get('valid_until_ns') != command['valid_until_ns']:
        raise ValueError('admitted deadline mismatch')
    terminal = terminals[0]
    if terminal.get('status') == 'completed' and terminal.get('steps_completed') != len(command['steps']):
        raise ValueError('completed step count mismatch')
    for field, expected in [('terminal', terminal), ('last_reply', submit['reply']), ('continuation_batch', submit['reply'])]:
        if not exact(report.get(field), expected):
            raise ValueError('contradictory or missing ' + field)
    return {'program_id': identifier, 'request_id': sq['request_id'], 'terminal': terminal,
            'meaning': 'internally consistent recorded program binding; not task success, provenance, current lease or input approval'}


def build(data):
    report = json.loads(data)
    result = index(data)
    result['format'] = 'decision-receipt-v2'
    result['program_binding'] = None
    try:
        result['program_binding'] = binding(report)
    except (KeyError, TypeError, ValueError, IndexError) as exc:
        result['attention'].append({'path': [], 'reason': 'program binding unverified', 'detail': str(exc)})
    def visit(value, path):
        if isinstance(value, dict):
            for key, child in value.items():
                if (key in ('error', 'exception') and child is not None and child is not False and child != '') or (key in ('success', 'verified', 'exact', 'focus_samples_match') and child is False):
                    result['attention'].append({'path': path + [key], 'reason': 'nested exception or negative evidence'})
                visit(child, path + [key])
        elif isinstance(value, list):
            for i, child in enumerate(value):
                visit(child, path + [i])
    visit(report, [])
    result['detail_review_required'] = bool(result['attention'])
    result['limits'] = 'Binding checks only recorded consistency, not authenticity or full nested schema semantics. No attention is not approval. Unknown nested fields may need manual review.'
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    with args.source.open('rb') as stream:
        data = stream.read(MAX_SOURCE + 1)
    print(json.dumps(build(data), ensure_ascii=False, allow_nan=False))
