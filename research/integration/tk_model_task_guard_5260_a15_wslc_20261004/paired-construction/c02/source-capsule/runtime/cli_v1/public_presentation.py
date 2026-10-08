"""Opt-in projection of repeated successful-dispatch program provenance."""
from copy import deepcopy
import hashlib
import json

def _source_projection(view):
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


from runtime.core_v1.sequence import expand_text_gaps
def encode(v):
    return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def brief_public_report(view):
    full=deepcopy(view)
    # Reuse the archived success/failure gate unchanged.
    base=_source_projection(view)
    if base.get('presentation',{}).get('returned')!='brief':return full
    try:
        raw=view['receipt']['source']['raw_report'];execution=raw['result']['execution']
        comp=raw['compilation']
        if comp['kind']!='bounded_text_gap':return full
        operations,mapping=expand_text_gaps(comp['source_program']['ops'])
        if encode(mapping)!=encode(comp['operation_sources']):return full
        if encode(execution['completed_ops'])!=encode(list(range(len(operations)))):return full
        waits=execution['waits']
        expected=[(i,o['timeout_ms']) for i,o in enumerate(operations) if o['op']=='wait_update']
        if len(waits)!=len(expected) or not waits:return full
        keys={'operation_index','requested_ms','started_ns','completed','kind','update_observed','ended_ns'}
        for w,(index,requested) in zip(waits,expected):
            if set(w)!=keys:return full
            if any(type(w[n]) is not int for n in ('operation_index','requested_ms','started_ns','ended_ns')):return full
            if w['operation_index']!=index or w['requested_ms']!=requested:return full
            if w['started_ns']<0 or w['ended_ns']<w['started_ns']:return full
            if w['completed'] is not True or w['kind']!='fixed_delay' or w['update_observed'] is not None:return full
        target=base['receipt']['source']['report_projection']
        def marker(value):
            return {'sha256':hashlib.sha256(encode(value)).hexdigest(),'bytes':len(encode(value)),'encoding':'canonical JSON, UTF-8, sorted keys, compact, ensure_ascii=true'}
        target['result']['execution'].pop('waits')
        target['result']['execution']['wait_summary']={
            'count':len(waits),'requested_ms_total':sum(w['requested_ms'] for w in waits),
            'recorded_elapsed_ns_total':sum(w['ended_ns']-w['started_ns'] for w in waits),
            'kind':'fixed_delay','update_observed':None,'all_completed':True,
            'omitted_records':marker(waits)}
        target['compilation'].pop('operation_sources')
        target['compilation']['operation_sources_omitted']={'count':len(mapping),**marker(mapping)}
        base['receipt']['schema']='agent-interface/receipt-view-paced-brief-v1'
        base['presentation']['scope']='Partial success-only projection: source programs, wait records and expansion map omitted. Not lossless or task success.'
        base['presentation']['omitted_paths'] += ['/receipt/source/raw_report/result/execution/waits','/receipt/source/raw_report/compilation/operation_sources']
        base['receipt']['scope']='Partial retained report projection; full report requires explicit retrieval. No input or freshness granted.'
        if len(encode(base))>=len(encode(view)):return full
        return base
    except (KeyError,TypeError,ValueError,AttributeError):return full
