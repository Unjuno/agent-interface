"""Opt-in projection of repeated successful-dispatch program provenance."""
from copy import deepcopy
import hashlib
import json

def brief_public_report(view):
    """Omit only known source-program copies; keep all execution evidence.

    The original retained report remains authoritative. Exact-call retrieval is
    required to recover omitted programs. No task success or authority is added.
    """
    full = deepcopy(view)
    full['presentation'] = {'requested': 'brief', 'returned': 'full',
                            'reason': 'critical_or_unsupported_result'}
    try:
        receipt = view['receipt']
        raw = receipt['source']['raw_report']
        result = raw['result']
        outcome = view['outcome_summary']
        execution = result['execution']
        if (receipt['schema'] != 'agent-interface/receipt-view-v3-report-ref'
            or raw['schema'] != 'agent-interface/runtime-dispatch-result-v1'
            or raw['status'] != 'returned' or result['status'] != 'completed'
            or result['admission'] != 'accepted'
            or result['recovery_required'] is not False
            or outcome['execution_status'] != 'completed'
            or outcome['input_release_verified'] is not True
            or outcome.get('error') is not None
            or outcome.get('cleanup_error') is not None
            or outcome.get('execution_error') is not None
            or view.get('persistence_error') is not None
            or view.get('image_status') not in ('image', 'not_requested')
            or not execution['releases']
            or any(r.get('verified') is not True or r.get('keys_down') != []
                   or r.get('buttons_down') != [] or 'error' in r
                   for r in execution['releases'])
            or any(w.get('completed') is not True or 'error' in w for w in execution['waits'])
            or any('artifact_error' in o or 'error' in o for o in execution['observations'])
            or not isinstance(view['call_id'], str) or not view['call_id']
            or 'presentation' in view):
            return full
        if view.get('session', {}).get('recovery_required', False) is not False:
            return full
        projected = deepcopy(view)
        target = projected['receipt']['source']['raw_report']
        omitted = []
        for name, kind in (('normalization', 'explicit_observation_region'),
                           ('compilation', 'bounded_text_gap')):
            section = raw.get(name)
            if not isinstance(section, dict) or section.get('kind') != kind:
                continue
            program = section.get('source_program')
            if not isinstance(program, dict) or program.get('schema') != 'agent-interface/program-v1':
                continue
            encoded = json.dumps(program, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
            target[name].pop('source_program')
            # Use a new, explicit marker, never an executable program or local JSON reference.
            if 'source_program_omitted' in section:
                return full
            target[name]['source_program_omitted'] = {
                'sha256': hashlib.sha256(encoded).hexdigest(),
                'encoding': 'UTF-8 canonical JSON: sorted keys, compact separators, ensure_ascii=true',
                'bytes': len(encoded)}
            omitted.append('/receipt/source/raw_report/' + name + '/source_program')
        if not omitted:
            return full
        projected['receipt']['schema'] = 'agent-interface/receipt-view-program-brief-v1'
        source = projected['receipt']['source']
        source['report_projection'] = source.pop('raw_report')
        projected['receipt']['report'] = {'report_ref': '/source/report_projection'}
        projected['receipt']['report_reference'] = '/source/report_projection'
        projected['receipt']['reference_scope'] = 'Partial report projection only; original source digest identifies the retained full report.'
        projected['presentation'] = {
            'requested': 'brief', 'returned': 'brief',
            'scope': 'Source program copies omitted; execution evidence unchanged. Not lossless or task success.',
            'omitted_paths': omitted,
            'retrieve': {'tool': 'interface_results', 'arguments': {
                'call_id': view['call_id'], 'include_image': False,
                'compact': True, 'report_refs': True, 'detail': 'full'}}}
        size = lambda obj: len(json.dumps(obj, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())
        if size(projected) >= size(view):
            full['presentation']['reason'] = 'not_smaller'
            return full
        return projected
    except (KeyError, TypeError, ValueError, AttributeError):
        return full
