"""Read-only workload accounting of hash-bound relay replies, not task scoring."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
from .host_timing import summarize as summarize_timing


def reported_dispatch(reply):
    """Classify only explicit public dispatch evidence, never infer input effects."""
    unknown = {'classification': 'unclassified'}
    if reply.get('status') == 'refused':
        if reply.get('dispatched') is False:
            return {'classification': 'relay_refused_before_dispatch'}
        return unknown
    if reply.get('status') == 'unknown_requires_reconciliation':
        return {'classification': 'unknown_requires_reconciliation'}
    result = reply.get('result')
    if reply.get('status') != 'returned' or not isinstance(result, dict):
        return unknown
    blocks = result.get('content')
    if not isinstance(blocks, list):return unknown
    texts = [b.get('text') for b in blocks if isinstance(b, dict) and b.get('type') == 'text']
    if len(texts) != 1 or not isinstance(texts[0], str):return unknown
    try:view = json.loads(texts[0])
    except ValueError:return unknown
    if not isinstance(view, dict) or view.get('schema') != 'agent-interface/review-v1':return unknown
    outcome = view.get('outcome_summary')
    if not isinstance(outcome, dict):return unknown
    status = outcome.get('execution_status')
    if status not in ('completed', 'refused', 'execution_failed'):
        return unknown
    receipt = view.get('receipt')
    if not isinstance(receipt, dict):return unknown
    schema = receipt.get('schema')
    if schema == 'agent-interface/receipt-view-dispatch-summary-v1':
        if status != 'completed':return unknown
    elif schema in ('agent-interface/receipt-view-v3', 'agent-interface/receipt-view-v3-report-ref'):
        source = receipt.get('source')
        raw = source.get('raw_report') if isinstance(source, dict) else None
        raw_result = raw.get('result') if isinstance(raw, dict) else None
        if not isinstance(raw_result, dict) or raw_result.get('status') != status:return unknown
    else:return unknown
    release = outcome.get('input_release_verified')
    row = {'classification': 'reported_' + status,
           'input_release_verified': release if type(release) is bool else None}
    inspection = view.get('post_dispatch_inspection')
    if isinstance(inspection, dict):
        row['inspection'] = ('error' if inspection.get('error') is not None else
                             'skipped' if inspection.get('status') == 'skipped' else
                             'review_candidate' if isinstance(inspection.get('review_request'), dict) else 'unclassified')
    return row


def summarize(directory):
    directory=Path(directory)
    timing=summarize_timing(directory)
    calls=[]
    for call in timing['calls']:
        row={'attempt':call['attempt'],'tool':call['tool'],
             'reply_received':call['reply_ms'] is not None,
             'completed_presentations':sum(p['completed_ms'] is not None for p in call['presentations']),
             'declared_reviews':len(call['reviews'])}
        if row['reply_received']:
            name=f"reply-{call['attempt']}.json"
            raw=(directory/name).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=timing['input_sha256'][name]:
                raise ValueError('reply changed after timeline validation')
            reply=json.loads(raw)
            if call['tool']=='interface_dispatch':row['dispatch']=reported_dispatch(reply)
        elif call['tool']=='interface_dispatch':
            row['dispatch']={'classification':'no_reply_outcome_unknown'}
        calls.append(row)
    counts=Counter(r['dispatch']['classification'] for r in calls if 'dispatch' in r)
    return {'schema':'agent-interface/retained-workload-v1',
            'scope':'One retained host lifetime. Counts reported receipts, not successful tasks or input effects.',
            'timeline_status':timing['timeline_status'],
            'calls_by_tool':dict(sorted(Counter(r['tool'] for r in calls).items())),
            'dispatch_receipts':dict(sorted(counts.items())),
            'call_count':len(calls),'calls':calls,
            'time_partition':timing['time_partition'],
            'unmeasured':['task correctness without independent oracle','repair/replay intent and recovery cost attribution',
                          'first useful model feedback','semantic completion','model tokens and cost','matched speedup'],
            'input_sha256':timing['input_sha256']}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('transport_directory',type=Path)
    print(json.dumps(summarize(parser.parse_args().transport_directory),indent=2,allow_nan=False))

if __name__=='__main__':main()
