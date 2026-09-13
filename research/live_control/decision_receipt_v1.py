"""Offline report index for human/model review; never a continuation authority."""
import argparse
import collections
import json
from pathlib import Path
from report_pages_v2 import digest, MAX_SOURCE

ROUTINE = {'command', 'clock', 'accepted', 'step_started', 'step_completed',
           'pointer_admission', 'input_admission', 'keys_held', 'observation', 'settle_result'}
KNOWN_FIELDS = set('event command received_ns emit_started_ns emitted_ns runtime_ns sequence id steps valid_until_ns accepted_ns step operation issued_ns payload admitted_ns input_ack_ns surface key keys image image_reused image_prepare_ns image_ready_ns context context_ns capture_ns input_focus_before input_focus_after focus_samples_match pointer_binding pointer_context_before pointer_context_after capture_ms wire_bytes exact semantic_completion completed_ns reason samples elapsed_ms quiet_ms timeout_ms'.split())
REPORT_FIELDS = {'state', 'exchanges', 'program_sent', 'source_image', 'image', 'terminal',
                 'last_reply', 'continuation_batch', 'reason', 'authority'}


def build(data):
    if len(data) > MAX_SOURCE:
        raise ValueError('report exceeds source cap')
    report = json.loads(data)
    if not isinstance(report, dict) or not isinstance(report.get('exchanges'), list):
        raise ValueError('original caller report required')
    source = {'sha256': digest(data), 'bytes': len(data)}
    groups, attention, terminals = collections.defaultdict(list), [], []
    for key in sorted(set(report) - REPORT_FIELDS):
        attention.append({'path': [key], 'reason': 'unknown report field'})
    if report.get('state') != 'terminal' or report.get('reason'):
        attention.append({'path': [], 'reason': 'caller unresolved or reports reason'})
    for i, exchange in enumerate(report['exchanges']):
        path = ['exchanges', i, 'reply']
        reply = exchange.get('reply')
        if not isinstance(reply, dict) or not isinstance(reply.get('records'), list):
            attention.append({'path': path, 'reason': 'missing reply/records'})
            continue
        after, cursor = exchange.get('request', {}).get('after'), reply.get('cursor')
        if type(after) is not int or type(cursor) is not int or cursor != after + len(reply['records']) or reply.get('status') != 'boundary':
            attention.append({'path': path, 'reason': 'reply boundary/prefix unresolved'})
        for j, event in enumerate(reply['records']):
            ref = path + ['records', j]
            if not isinstance(event, dict):
                attention.append({'path': ref, 'reason': 'non-object event'})
                continue
            kind = event.get('event')
            groups[str(kind)].append(ref)
            if kind == 'terminal':
                terminals.append({'path': ref, 'record': event})
                if event.get('status') != 'completed' or event.get('error') is not None or event.get('release', {}).get('verified') is not True:
                    attention.append({'path': ref, 'reason': 'terminal interruption/error/unverified release'})
            elif kind not in ROUTINE:
                attention.append({'path': ref, 'reason': 'event requires detail review'})
            else:
                unknown = sorted(set(event) - KNOWN_FIELDS)
                if unknown:
                    attention.append({'path': ref, 'reason': 'unknown event fields', 'fields': unknown})
                if event.get('exact') is False or event.get('focus_samples_match') is False:
                    attention.append({'path': ref, 'reason': 'inexact image or focus mismatch'})
                if kind == 'settle_result' and event.get('reason') != 'pixel_quiet':
                    attention.append({'path': ref, 'reason': 'settle did not report quiet'})
    if report.get('terminal') is not None and not any(t['record'] == report['terminal'] for t in terminals):
        attention.append({'path': ['terminal'], 'reason': 'top terminal absent from exchange evidence'})
    return {'format': 'decision-receipt-v1', 'source': source,
            'reported_state': report.get('state'), 'reported_reason': report.get('reason'),
            'program_write_may_have_been_attempted': report.get('program_sent'),
            'terminals': terminals, 'image': report.get('image'),
            'event_index': {kind: {'count': len(paths), 'paths': paths} for kind, paths in groups.items()},
            'attention': attention, 'detail_review_required': bool(attention),
            'task_success': 'unknown; program completion is not independent task scoring',
            'coverage': 'Index of exchange events only; routine payloads and other report fields remain in source. Not full review or schema validation.',
            'authority': 'none; no new input approval, refreshed image, or model receipt',
            'limits': 'Nested schemas/semantic anomalies are not fully validated; absence of attention does not prove safety or completeness.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    with args.source.open('rb') as stream:
        data = stream.read(MAX_SOURCE + 1)
    print(json.dumps(build(data), ensure_ascii=False, allow_nan=False))


if __name__ == '__main__':
    main()
