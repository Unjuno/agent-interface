"""New query uses existing once-only forwarding and scoped cursor boundaries."""
import hashlib,json
from pathlib import Path
from command_once_v3 import CommandOnce
from event_cursor_v6 import EventCursor
HERE=Path(__file__).resolve().parent;out=HERE/'results/checkpoint-identity-01';out.mkdir(exist_ok=False)
written=[];sender=CommandOnce(written.append)
command=dict(op='effect_checkpoint',contract=dict(kind='saved_form_value',expected='value'))
assert sender.send('query',command)['state']=='stdin_flushed'
assert sender.send('query',command)['replayed'] is True and len(written)==1
for value in (dict(op='unsupported'),dict(command,contract=dict(kind='saved_form_value',expected='changed'))):
    try:sender.send('query',value)
    except ValueError:pass
    else:raise AssertionError('invalid/conflicting query accepted')
assert len(written)==1
cursor=EventCursor()
cursor.append(dict(event='effect_checkpoint',transport_request_id='other',evidence=dict(status='VERIFIED')))
cursor.append(dict(event='effect_checkpoint',transport_request_id='query',evidence=dict(status='UNKNOWN')))
reply=cursor.read_until(after=0,events=['effect_checkpoint'],timeout=0,request_id='query')
assert reply['status']=='boundary' and len(reply['records'])==2 and reply['records'][-1]['evidence']['status']=='UNKNOWN'
missing=EventCursor();missing.append(dict(event='effect_checkpoint',evidence=dict(status='VERIFIED')))
assert missing.read_until(after=0,events=['effect_checkpoint'],timeout=0,request_id='query')['status']=='identity_unknown'
result=dict(one_forwarded_query=True,conflicting_and_unsupported_rejected=True,
    other_request_prefix_retained=True,scoped_unknown_preserved=True,missing_identity_not_accepted=True)
(out/'results.json').write_text(json.dumps(result,indent=2)+'\n')
(out/'sources.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in
    (Path(__file__),HERE/'command_once_v3.py',HERE/'event_cursor_v6.py',HERE/'request_boundary_v3.py')},indent=2)+'\n')
print(json.dumps(result))
