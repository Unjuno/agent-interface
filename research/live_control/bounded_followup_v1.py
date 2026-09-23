"""One optional terminal read: 400ms server wait, 650ms absolute socket deadline."""
import copy
import time
from stopped_client_v1 import PendingAction
from receipt_image import select_image
from unix_json_deadline import exchange


def collect(socket_path, previous, root):
    report=copy.deepcopy(previous);history=report['exchanges']
    submit=history[1]['request'];command=submit['command']
    if command.get('op')!='submit':raise ValueError('recorded submit required')
    tracker=PendingAction(command['id'],submit['after'])
    for item in history[1:]:
        if 'reply' in item:tracker.ingest(item['request']['after'],item['reply'])
    if tracker.view()['state']!='input_stopped_capture_pending':
        raise ValueError('verified pending interruption required')
    request=tracker.poll_request(.4)
    attempt=dict(request=request,started_ns=time.perf_counter_ns())
    history.append(attempt)
    try:
        reply=exchange(socket_path,request,timeout=.65)
        attempt['reply']=reply
        tracker.ingest(request['after'],reply)
        report['last_reply']=reply;report['continuation_batch']=reply
    except (TimeoutError,EOFError,OSError,ValueError) as exc:
        # This attempt contains no command. No cursor is advanced without a reply.
        attempt['read_error']=dict(type=type(exc).__name__,message=str(exc))
    attempt['returned_ns']=time.perf_counter_ns()
    state=tracker.view();report.update(state=state['state'],lifecycle=state)
    if tracker.terminal is not None:report['terminal']=tracker.terminal
    else:report.pop('terminal',None)
    received=[e for item in history[1:] for e in item.get('reply',{}).get('records',[])]
    report['image']=select_image(dict(records=received),root)
    report['bounded_followup']=dict(server_wait_ms=400,socket_deadline_ms=650,
        attempt_elapsed_ms=(attempt['returned_ns']-attempt['started_ns'])/1e6,
        read_error=attempt.get('read_error'),
        scope='one read only; no command, input retry or authority renewal; serialization/rendering outside I/O deadline')
    return report
