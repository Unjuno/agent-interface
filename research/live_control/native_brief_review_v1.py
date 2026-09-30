"""Opt-in normal-result presentation using the existing primary-review projection."""
import copy
import json
from native_primary_review_v1 import receipt_summary
from receipt_references import expand_native_receipt, compact_native_receipt


def brief_native_review(view):
    result = copy.deepcopy(view)
    result['presentation'] = {'requested': 'brief', 'returned': 'full',
                              'reason': 'critical_or_unsupported_result'}
    try:
        receipt = expand_native_receipt(view['receipt'])
        report = receipt['native_result']
        action = report['action']
        execution = action['result']['execution']
        checks = action['result']['guard_checks']
        releases = execution['releases']
        if (view.get('image_status') != 'image'
                or view.get('continuation', {}).get('status') in ('needs_review', 'observation_required')
                or report.get('status') != 'boundary' or 'target_refusal' in report
                or 'review_recovery' in action or 'review_recovery' in report.get('observation', {})
                or action['result'].get('status') != 'completed'
                or action['result'].get('recovery_required') is not False
                or action['feedback'].get('status') != 'matched'
                or action['window_review'].get('status') != 'reviewed'
                or any('error' in row for row in (action, action['result'], action['feedback'], action['window_review']))
                or execution.get('observations') != []
                or not checks or any(c.get('status') != 'VALID' for c in checks)
                or not releases or any(r.get('verified') is not True for r in releases)
                or any(w.get('completed') is not True for w in execution.get('waits', []))):
            return result
        feedback_sample_count = len(action['feedback'].get('samples', []))
        projected = receipt_summary({'direct': {'result': action['result']},
                                     'feedback': action['feedback']})
        action['result'] = projected['operations']['direct']
        action['feedback'] = projected['feedback']
        summary = compact_native_receipt(receipt)
        result.pop('receipt')
        result['receipt_summary'] = summary
        result['presentation'] = {
            'requested': 'brief', 'returned': 'brief',
            'scope': 'normal-result projection; not a lossless replacement for the full receipt',
            'full_receipt': view['receipt']['source'],
            'retrieve': {'tool': 'native_resume', 'arguments': {
                'stage': report['stage'], 'decision_sha256': report['decision_sha256'],
                'include_image': False, 'detail': 'full'}},
            'omitted_detail_counts': {'guard_checks': len(checks),
                'completed_ops': len(execution['completed_ops']),
                'waits': len(execution.get('waits', [])),
                'feedback_samples': feedback_sample_count},
        }
        size = lambda value: len(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
        if size(result) >= size(view):
            unchanged = copy.deepcopy(view)
            unchanged['presentation'] = {'requested': 'brief', 'returned': 'full', 'reason': 'not_smaller'}
            return unchanged
        return result
    except (KeyError, IndexError, TypeError, ValueError, AttributeError):
        # New or malformed shapes remain fully visible; never upgrade an outcome.
        fallback = copy.deepcopy(view)
        fallback['presentation'] = {'requested': 'brief', 'returned': 'full',
                                    'reason': 'critical_or_unsupported_result'}
        return fallback
