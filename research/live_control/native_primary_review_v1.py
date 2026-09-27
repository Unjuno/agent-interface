"""Retain an explicit primary-model outcome review before the next task.

This records the caller's interpretation, not independent task correctness.
No model, input, retry, evaluator or automatic acknowledgement is invoked here.
"""
import json
import time


def receipt_summary(row):
    """Project recorded outcomes; never infer task success from completion."""
    operations = {}
    for name in ('navigation', 'direct', 'entered', 'repaired_enter', 'saved'):
        if name not in row:
            continue
        value = row[name]
        wrapper = value.get('result', {}) if name == 'navigation' else value
        result = wrapper.get('result', {}) if name in ('navigation', 'direct') else wrapper
        summary = {k:v for k,v in result.items()
                   if k not in ('execution', 'guard_checks', 'required_capabilities')}
        if name in ('navigation', 'direct'):
            summary['transport'] = {k:v for k,v in wrapper.items() if k != 'result'}
        execution = result.get('execution', {})
        summary['execution'] = {k:v for k,v in execution.items()
                                if k not in ('observations', 'completed_ops', 'waits')}
        operations[name] = summary
    feedback = {k:v for k,v in row.get('feedback', {}).items()
                if k not in ('observation', 'samples')}
    return {'scope':'receipt projection; full guard/capture/wait records in receipt_file',
            'operations':operations, 'feedback':feedback,
            'refusal_emissions':row.get('refusal_emissions'),
            'task_success':None, 'authority':'none'}


def grounding_notice(name, source, request_file, *, prior_receipt=None, receipt_file=None):
    notice = {'needs_grounding':name, 'source_sequence':source['sequence'],
              'image':source['native']['artifact']['path'], 'request_file':str(request_file)}
    if prior_receipt is not None:
        if receipt_file is None:
            raise ValueError('full receipt reference required for grounding summary')
        notice.update(receipt_file=str(receipt_file), receipt_summary=receipt_summary(prior_receipt))
    return notice


def validate_review(value, task_id, source_sequence):
    if not isinstance(value, dict) or set(value) != {'task_id', 'source_sequence', 'outcome', 'reason'}:
        raise ValueError('exact primary review fields required')
    if value['task_id'] != task_id or type(value['source_sequence']) is not int or value['source_sequence'] != source_sequence:
        raise ValueError('primary review task/source mismatch')
    if value['outcome'] not in ('complete', 'uncertain', 'failed'):
        raise ValueError('explicit primary outcome required')
    if not isinstance(value['reason'], str) or not value['reason'].strip() or len(value['reason']) > 2000:
        raise ValueError('bounded nonempty review reason required')
    return value


def review_task(out, task_id, source, row, *, timeout=300):
    decision_path = out/(task_id+'-primary-review.json')
    result_path = out/(task_id+'-primary-review-result.json')
    request = {'task_id': task_id, 'source_sequence': source['sequence'],
               'image': source['native']['artifact']['path'],
               'source': source, 'task_receipt': row,
               'review_requested_ns': time.monotonic_ns(),
               'decision_file': str(decision_path),
               'authority': 'none', 'scope': 'primary interpretation; not independent scoring'}
    with (out/(task_id+'-primary-review-request.json')).open('x') as stream:
        json.dump(request, stream, indent=2)
    if decision_path.exists():
        raise ValueError('primary review decision predates request')
    print(json.dumps({'needs_primary_review': task_id, 'source_sequence': source['sequence'],
                      'image': request['image'], 'request_file': str(decision_path),
                      'receipt_file': str(out/(task_id+'-primary-review-request.json')),
                      'receipt_summary': receipt_summary(row)}), flush=True)
    end = time.monotonic()+timeout
    result = {'status':'unavailable', 'review_requested_ns':request['review_requested_ns']}
    try:
        while not decision_path.exists():
            if time.monotonic() >= end:
                raise TimeoutError('primary review timeout; no next task')
            time.sleep(.05)
        result['review_received_ns'] = time.monotonic_ns()
        decision = validate_review(json.loads(decision_path.read_text()), task_id, source['sequence'])
        result.update(status='reviewed', decision=decision)
        result['action_to_review_ms'] = (result['review_received_ns']-row['action_started_ns'])/1e6
        result['feedback_to_review_ms'] = (result['review_received_ns']-row['feedback_received_ns'])/1e6
        if decision['outcome'] != 'complete':
            raise RuntimeError('primary outcome '+decision['outcome']+'; no next task')
        return result
    except Exception as error:
        result['error'] = str(error)
        raise
    finally:
        with result_path.open('x') as stream:
            json.dump(result, stream, indent=2)
