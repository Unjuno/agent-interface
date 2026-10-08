from pathlib import Path
import json, hashlib, copy

base = Path(__file__).resolve().parent
case = base / '01-pending'
def read(p): return json.loads(p.read_text())
def require(ok, reason):
    if not ok: raise ValueError(reason)
def audit(replies, events, requests):
    require([r['request']['op'] for r in replies] == ['observe','review','mint','input','review','observe_after_stop','review','close'], 'command order')
    require([r['tool'] for r in requests] == ['interface_guarded_observe','interface_guarded_mint','interface_guarded_input','interface_guarded_observe','interface_close'], 'public request order')
    require(requests[3]['arguments'] == {}, 'read-only arguments')
    require(events[0]['event'] == 'save' and events[0]['token'] == 't1001070' and events[1]['event'] == 'app_ack' and events[1]['status'] == 'SAVED' and len(events) == 2, 'exact once app effects')
    pending, fresh = replies[3], replies[5]
    require(pending['isError'] is True and pending['metadata']['result']['status'] == 'completed' and pending['metadata']['feedback']['status'] == 'pending', 'completed input pending cue')
    require(all(r['caller_state']['stopped'] == 'unexpected MCP refusal' for r in replies[3:]), 'sticky STOP')
    require(fresh['isError'] is False and fresh['metadata']['status'] == 'observed' and fresh['metadata']['input_dispatched'] is False, 'read-only returned')
    require(pending['metadata']['source']['capture_ns'] < events[1]['ns'] < fresh['metadata']['source']['capture_ns'], 'capture acknowledgment ordering')
    require(events[0]['ns'] < events[1]['ns'], 'app ordering')
    require(pending['metadata']['source']['sequence'] == 6 and fresh['metadata']['source']['sequence'] == 7, 'fresh sequence')
    require(len({r['metadata']['session']['session_id'] for r in (replies[0], pending, fresh)}) == 1, 'same session')

replies = [read(p) for p in sorted((case/'replies').glob('*.json'))]
requests = [read(case/'host'/f'request-{i}.json') for i in range(1,6)]
events = [json.loads(line) for line in (case/'events.jsonl').read_text().splitlines()]
require(read(case/'cleanup.json')['host_exit'] == 0, 'host cleanup')
require(all(isinstance(n,int) for n in read(case/'cleanup.json')['child_exit_codes']), 'children terminal')
require(read(case/'host-terminal.json')['exit']['code'] == 0, 'host terminal')
audit(replies, events, requests)
for index, attempt in [(0,1),(2,2),(3,3),(5,4),(7,5)]:
    raw = read(case/'host'/f'reply-{attempt}.json')['result']
    text = next(b['text'] for b in raw['content'] if b['type']=='text')
    require(json.loads(text) == replies[index]['metadata'], 'original host metadata')
    require(raw['isError'] == replies[index]['isError'], 'original error flag')
for index in (0,3,5):
    row = replies[index]
    artifact = row['metadata']['source']['native']['artifact']
    original = Path(artifact['path']).read_bytes()
    primary = Path(row['image_path']).read_bytes()
    require(primary == original and hashlib.sha256(primary).hexdigest() == artifact['sha256'], 'original primary PNG')
session = next((case/'calls').glob('guarded-session-*'))
require(len(list(session.glob('observation-*.json'))) == 7, 'seven captures')
require(len(list(session.glob('program-guarded-*.json'))) == 1, 'one native program')
mutations = []
for name in ['clear_stop','duplicate_save','wrong_token','observe_input','stale_capture','extra_request']:
    rr, ee, qq = copy.deepcopy((replies,events,requests))
    if name == 'clear_stop': rr[5]['caller_state']['stopped'] = None
    elif name == 'duplicate_save': ee.append(copy.deepcopy(ee[0]))
    elif name == 'wrong_token': ee[0]['token'] = 'wrong'
    elif name == 'observe_input': rr[5]['metadata']['input_dispatched'] = True
    elif name == 'stale_capture': rr[5]['metadata']['source']['capture_ns'] = ee[1]['ns']-1
    else: qq.append(copy.deepcopy(qq[2]))
    try: audit(rr,ee,qq)
    except ValueError: mutations.append(name)
    else: raise ValueError('mutation accepted: '+name)
summary = dict(status='PASS',source_revision='4dced48b32a439c52d2c9aea10954cdc2035cfb4', public_requests=5, primary_images=3, captures=7, native_programs=1, save_events=1, ack_events=1, stop_cleared=False, rejected_mutations=mutations, app_ack_delay_ms=(events[1]['ns']-events[0]['ns'])/1e6, later_capture_after_ack_ms=(replies[5]['metadata']['source']['capture_ns']-events[1]['ns'])/1e6, model_tokens=None, billing=None, comparative_efficiency='NOT_MEASURED')
(base/'audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
