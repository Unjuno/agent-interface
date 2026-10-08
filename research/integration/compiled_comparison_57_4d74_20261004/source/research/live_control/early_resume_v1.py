"""One read-only continuation of a recorded early exchange; no implicit loop."""
import copy
import time
from stopped_client_v1 import PendingAction
from receipt_image import select_image


def resume(query, previous, root):
    report=copy.deepcopy(previous)
    exchanges=report['exchanges']
    submit=exchanges[1]['request'];command=submit['command']
    assert command['op']=='submit'
    tracker=PendingAction(command['id'],submit['after'])
    for item in exchanges[1:]:tracker.ingest(item['request']['after'],item['reply'])
    request=tracker.poll_request(5)
    started=time.perf_counter_ns();reply=query(request);returned=time.perf_counter_ns()
    exchanges.append(dict(request=request,reply=reply,started_ns=started,returned_ns=returned))
    lifecycle=tracker.ingest(request['after'],reply)
    report.update(state=lifecycle['state'],lifecycle=lifecycle,last_reply=reply,continuation_batch=reply)
    if tracker.terminal is not None:report['terminal']=tracker.terminal
    # Only received observations are considered; no capture or stale image substitution.
    report['image']=select_image(reply,root)
    return report
