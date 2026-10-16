"""Actual AF_UNIX round trips during a synthetic blocked capture."""
import json
import subprocess
import sys
import time
import threading
import uuid
from pathlib import Path
from unix_json_deadline import exchange
from event_scope import validate_scope as old_validate
from stopped_scope_v1 import boundary,validate_scope
from report_pages_v2 import digest
from stopped_client_v1 import PendingAction
from bounded_followup_v2 import collect

HERE=Path(__file__).resolve().parent
root=HERE/'results/bounded-followup-03';root.mkdir(exist_ok=False)
names=['probe_bounded_followup_v3.py','stopped_transport_entry_v1.py','stopped_transport_fixture_v1.py',
       'bounded_followup_v2.py','receipt_image.py','stopped_client_v1.py','stopped_socket_v1.py','stopped_cursor_v1.py','stopped_scope_v1.py','executor_v8.py',
       'post_release_observation_v2.py','command_once_v2.py','bounded_pipe_writer_v2.py','unix_json_deadline.py']
plan=dict(sources={n:digest((HERE/n).read_bytes()) for n in names},
    scope='Real private AF_UNIX transport and subprocess; synthetic backend capture gate, not actual X11 or model latency')
(root/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
try:old_validate('fault',['input_stopped'])
except ValueError:pass
else:raise AssertionError('baseline unexpectedly supports boundary')
validate_scope('fault',['input_stopped','terminal'])
assert boundary(dict(event='input_stopped',id='other'),['input_stopped'],'fault') is None
assert boundary(dict(event='input_stopped'),['input_stopped'],'fault')=='identity_unknown'
stderr=(root/'stderr.txt').open('w')
process=subprocess.Popen([sys.executable,str(HERE/'stopped_transport_entry_v1.py'),'serve','--',str(root)],stdout=subprocess.PIPE,stderr=stderr,text=True)
calls=[];cursor=0;tracker=None;states=[]
def query(socket,events,command=None,action=None,timeout=2):
    global cursor
    q=dict(after=cursor,events=events,timeout=timeout)
    if action:q['action_id']=action
    if command:q.update(command=command,request_id=uuid.uuid4().hex)
    started=time.perf_counter_ns();r=exchange(socket,q,timeout=4);returned=time.perf_counter_ns()
    calls.append(dict(request=q,reply=r,started_ns=started,returned_ns=returned))
    if tracker is not None and tracker.terminal is None:
        states.append(tracker.ingest(q['after'],r))
    cursor=r.get('cursor',cursor)
    return r
result={}
try:
    endpoint=json.loads(process.stdout.readline());socket=endpoint['socket']
    r=query(socket,['clock'],dict(op='clock'));now=r['records'][-1]['runtime_ns']
    tracker=PendingAction('fault',cursor)
    r=query(socket,['input_stopped','terminal'],dict(op='submit',id='fault',steps=[dict(op='fault'),dict(op='tail')],expected_sequence=1,valid_until_ns=now+5_000_000_000),action='fault')
    assert r['status']=='boundary' and r['records'][-1]['event']=='input_stopped'
    assert r['records'][-1]['decision_reason']=='focus_changed'
    early_returned_ns=calls[-1]['returned_ns']
    end=time.monotonic()+2
    while not (root/'capture-entered').exists():
        assert process.poll() is None and time.monotonic()<end
        time.sleep(.005)
    assert process.poll() is None
    previous=dict(exchanges=calls.copy(),state=tracker.view()['state'],last_reply=r)
    bounded=collect(socket,previous,root)
    extra=bounded['exchanges'][-1];calls.append(extra);cursor=extra['reply']['cursor']
    tracker.ingest(extra['request']['after'],extra['reply'])
    assert bounded['state']=='input_stopped_capture_pending'
    assert extra['reply']['status']=='timeout' and 'command' not in extra['request']
    assert bounded['bounded_followup']['attempt_elapsed_ms']<1000
    (root/'pending-report.json').write_text(json.dumps(bounded,indent=2)+'\n')
    gate_release_ns=time.perf_counter_ns()
    timer=threading.Timer(.18,lambda:(root/'release-capture').write_text('release'))
    timer.start()
    continued=collect(socket,dict(exchanges=calls.copy()),root)
    extra=continued['exchanges'][-1];calls.append(extra);cursor=extra['reply']['cursor'];r=extra['reply']
    tracker.ingest(extra['request']['after'],r)
    (root/'terminal-report.json').write_text(json.dumps(continued,indent=2)+'\n')
    assert continued['state']=='terminal_received'
    terminal=r['records'][-1]
    assert terminal['event']=='terminal' and terminal['status']=='needs_decision'
    assert terminal['post_release_observation']['captures']==2 and not terminal['post_release_observation']['stopped']
    assert tracker.view()['state']=='terminal_received'
    assert tracker.terminal==terminal
    query(socket,['terminal'],dict(op='finish'),timeout=.1)
    assert process.wait(timeout=3)==0
    raw=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
    covered=[]
    for call in calls:
        q,r=call['request'],call['reply'];a,b=q['after'],r['cursor']
        assert r['records']==raw[a:b] and b-a==len(r['records']);covered.extend(range(a,b))
    assert covered==list(range(len(raw)))
    assert not any(e['event']=='accepted' and e['id']=='premature' for e in raw)
    assert [e['step'] for e in raw if e['event']=='step_started']==[0]
    result=dict(success=True,early_notification_before_gate_release=early_returned_ns<gate_release_ns,
        no_terminal_while_capture_blocked=True,client_states=[r['state'] for r in states],uncancelled_capture_returns_within_wait=True,
        events=len(raw),calls=len(calls),exit_code=process.returncode, bounded_pending_ms=bounded['bounded_followup']['attempt_elapsed_ms'], bounded_terminal_ms=continued['bounded_followup']['attempt_elapsed_ms'],
        early_notification_roundtrip_ms=(calls[1]['returned_ns']-calls[1]['started_ns'])/1e6)
finally:
    (root/'release-capture').write_text('release')
    if process.poll() is None:
        process.terminate();process.wait(timeout=3)
    if 'timer' in globals():timer.join(2)
    stderr.close()
    (root/'client-states.json').write_text(json.dumps(states,indent=2)+'\n')
    (root/'calls.json').write_text(json.dumps(calls,indent=2)+'\n')
    (root/'report.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
