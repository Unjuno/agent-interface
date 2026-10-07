"""Expose servo feedback and distinguish its typed distance metric from exceptions."""
import argparse
import json
import math
from pathlib import Path
from decision_receipt_v3 import build as previous

TRACKING_FIELDS = frozenset(('status', 'error', 'margin', 'rival_error', 'source_observation',
                            'observation', 'frame_id', 'patch_sha256', 'box', 'delta',
                            'error_method', 'raw_error'))


def metric_at(report, path):
    # Recognize only tracking.error directly inside a servo_feedback event.
    # Arbitrary nested error values, including numeric exceptions, retain attention.
    if len(path) < 3 or path[-2:] != ['tracking', 'error']:
        return False
    try:
        event = report
        for key in path[:-2]:
            event = event[key]
        if not isinstance(event, dict) or event.get('event') != 'servo_feedback':
            return False
        tracking = event['tracking']
        value = tracking['error']
        return (set(tracking) <= TRACKING_FIELDS and tracking.get('status') == 'matched'
                and tracking.get('error_method') in ('raw', 'trimmed_fallback')
                and type(value) in (int, float) and math.isfinite(value) and 0 <= value <= 1)
    except (KeyError, IndexError, TypeError):
        return False


def build(data):
    result = previous(data)
    report = json.loads(data)
    result['format'] = 'decision-receipt-v4'
    result['tracking_metrics'] = []
    remaining = []
    for item in result['attention']:
        if item['reason'] == 'nested exception or negative evidence' and metric_at(report, item['path']):
            result['tracking_metrics'].append({'path': item['path'],
                'meaning': 'reported normalized image distance, not an exception; match status is not object identity or task success'})
        else:
            remaining.append(item)
    result['attention'] = remaining
    result['servo_feedback'] = []
    for path in result['event_index'].get('servo_feedback', {}).get('paths', []):
        value = report
        for key in path:
            value = value[key]
        result['servo_feedback'].append({'path': path, 'record': value})
    result['detail_review_required'] = bool(remaining)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('source', type=Path)
    args = parser.parse_args()
    from report_pages_v2 import MAX_SOURCE
    with args.source.open('rb') as stream:
        data = stream.read(MAX_SOURCE + 1)
    print(json.dumps(build(data), allow_nan=False))
