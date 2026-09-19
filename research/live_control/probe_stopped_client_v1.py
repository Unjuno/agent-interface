"""Lifecycle controls plus replay of real early-notification socket evidence."""
import copy
import json
from pathlib import Path
from stopped_client_v1 import PendingAction
from report_pages_v2 import digest

HERE=Path(__file__).resolve().parent;out=HERE/'results/stopped-client-01';out.mkdir(exist_ok=False)
release=dict(verified=True,keys_down=[],buttons_down=[])
accepted=dict(event='accepted',id='a')
stop=dict(event='input_stopped',id='a',release=release,decision_reason='focus_changed',interruption={'intent_token':'one'})
terminal=dict(event='terminal',id='a',release=release,status='needs_decision',decision_reason='focus_changed',interruption={'intent_token':'one'})
def reply(records,status='boundary',after=0):return dict(status=status,records=records,cursor=after+len(records))
rows=[]
def check(name,edits,expected):
    action=PendingAction('a',0)
    for after,r in edits:state=action.ingest(after,r)
    assert state['state']==expected,(name,state)
    assert state['input_authority']=='none'
    rows.append(dict(case=name,state=state))
check('same batch stop and terminal',[(0,reply([accepted,stop,terminal]))],'terminal_received')
check('timeout remains pending',[(0,reply([accepted,stop])),(2,reply([],status='timeout',after=2))],'input_stopped_capture_pending')
check('exact replay',[(0,reply([accepted,stop])),(0,reply([accepted,stop])),(2,reply([terminal],after=2))],'terminal_received')
foreign=dict(terminal,id='foreign')
check('foreign terminal ignored',[(0,reply([accepted,stop,foreign]))],'input_stopped_capture_pending')
check('missing admission',[(0,reply([stop]))],'needs_reconciliation')
check('gap',[(0,dict(status='gap',records=[],cursor=0))],'needs_reconciliation')
check('close pending',[(0,reply([accepted,stop],status='closed'))],'needs_reconciliation')
check('duplicate distinct stop',[(0,reply([accepted,stop,stop]))],'needs_reconciliation')
check('cause mismatch',[(0,reply([accepted,stop,dict(terminal,interruption={'intent_token':'two'})]))],'needs_reconciliation')
check('unverified stop',[(0,reply([accepted,dict(stop,release=dict(release,verified=False))]))],'needs_reconciliation')
check('future cursor',[(3,reply([],after=3))],'needs_reconciliation')
check('sticky rejection',[(0,reply([accepted,stop,dict(event='rejected',reason='busy'),terminal])),(3,reply([terminal],after=3))],'needs_reconciliation')
action=PendingAction('a',0);action.ingest(0,reply([accepted,stop]))
q=action.poll_request(.1);assert 'command' not in q and q['events']==['terminal'] and q['after']==2
calls_path=HERE/'results/stopped-transport-01/calls.json';calls=json.loads(calls_path.read_text())
action=PendingAction('fault',calls[1]['request']['after'])
first=action.ingest(calls[1]['request']['after'],calls[1]['reply'])
assert first['state']=='input_stopped_capture_pending'
waiting=action.ingest(calls[2]['request']['after'],calls[2]['reply'])
assert waiting['state']=='input_stopped_capture_pending'
uncertain=action.ingest(calls[3]['request']['after'],calls[3]['reply'])
assert uncertain['state']=='needs_reconciliation'  # Existing probe deliberately submitted while busy.
result=dict(success=True,cases=rows,real_socket_prefix_states=[first['state'],waiting['state'],uncertain['state']],
    evidence_sha256=digest(calls_path.read_bytes()),sources={n:digest((HERE/n).read_bytes()) for n in ['stopped_client_v1.py','probe_stopped_client_v1.py']},
    scope='Recorded lifecycle checks; no new GUI trial, admission authority or full schema/authenticity validation')
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(success=True,cases=len(rows),real_socket_prefix_states=result['real_socket_prefix_states'])))
