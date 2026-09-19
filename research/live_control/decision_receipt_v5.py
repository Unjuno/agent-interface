"""Bind early/followup reports using contiguous recorded reads; retain negative evidence."""
import copy
import json
from decision_receipt_v4 import build as previous
from decision_receipt_v2 import binding as old_binding,exact
from stopped_client_v1 import PendingAction


def binding(report):
    if report.get('state')!='terminal_received' or report.get('reason') or report.get('program_sent') is not True:
        raise ValueError('resolved attempted lifecycle required')
    xs=report['exchanges']
    if not isinstance(xs,list) or not 2<=len(xs)<=64:raise ValueError('bounded exchange history required')
    sq=xs[1]['request'];command=sq['command'];identifier=command['id']
    tracker=PendingAction(identifier,sq['after']);records=[];cursor=sq['after']
    for i,x in enumerate(xs[1:],1):
        q=x['request'];r=x['reply']
        if x.get('read_error') is not None:raise ValueError('read error requires review')
        if q['after']!=cursor:raise ValueError('noncontiguous followup')
        if i>1:
            if set(q)!={'after','events','action_id','timeout'} or q['events']!=['terminal'] or q['action_id']!=identifier:
                raise ValueError('only own command-free terminal reads may follow submit')
            if type(q['timeout']) not in (int,float) or not 0<=q['timeout']<=30:
                raise ValueError('invalid followup timeout')
            if any(e.get('event')=='command' for e in r['records']):raise ValueError('interleaved command')
        if r.get('status') not in ('boundary','timeout','batch_limit'):
            raise ValueError('unresolved read status')
        tracker.ingest(q['after'],r)
        if tracker.uncertainty:raise ValueError(tracker.uncertainty)
        records.extend(r['records']);cursor=r['cursor']
    lifecycle=tracker.view()
    if lifecycle['state']!='terminal_received' or not exact(lifecycle,report.get('lifecycle')):
        raise ValueError('lifecycle does not match received evidence')
    if not exact(report.get('terminal'),tracker.terminal):raise ValueError('terminal mismatch')
    if not exact(report.get('last_reply'),xs[-1]['reply']) or not exact(report.get('continuation_batch'),xs[-1]['reply']):
        raise ValueError('final reply copy mismatch')
    if not records or records[-1]!=tracker.terminal:raise ValueError('terminal must end received history')
    now=xs[0]['reply']['records'][-1]['runtime_ns']
    if type(command.get('valid_until_ns')) is not int or not 0<command['valid_until_ns']-now<=30_000_000_000:
        raise ValueError('deadline outside admission horizon')
    # Explicit internal projection only: all source slices have been checked above.
    # The receipt source hash and paths always refer to the unchanged input bytes.
    projected=copy.deepcopy(report);merged=copy.deepcopy(xs[1]['reply'])
    merged.update(status='boundary',records=records,cursor=cursor)
    projected.update(state='terminal',exchanges=copy.deepcopy(xs[:2]),last_reply=merged,continuation_batch=merged)
    projected['exchanges'][1]['reply']=merged
    result=old_binding(projected)
    result.update(recorded_exchanges=len(xs),projection='validated contiguous received slices; not a new socket reply',
                  lifecycle_state='terminal_received')
    return result


def build(data):
    result=previous(data);report=json.loads(data)
    result['format']='decision-receipt-v5'
    if report.get('state')!='terminal_received':return result
    try:
        verified=binding(report)
    except (KeyError,TypeError,ValueError,IndexError,AttributeError) as exc:
        result['attention'].append(dict(path=[],reason='lifecycle binding unverified',detail=str(exc)))
    else:
        result['program_binding']=verified
        result['attention']=[a for a in result['attention'] if not (a.get('path')==[] and
            a.get('reason') in ('program binding unverified','caller unresolved or reports reason'))]
    result['detail_review_required']=bool(result['attention'])
    return result
