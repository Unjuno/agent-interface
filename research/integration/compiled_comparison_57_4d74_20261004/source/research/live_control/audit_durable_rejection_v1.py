"""Check real process-loss recovery against runtime trace and saved application effect."""
import hashlib, json, sys, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from received_continuation_v1 import start, advance
from durable_submit_v2 import reconcile
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'observation_tiles'))
from tile_transport import Decoder


def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    r = HERE / 'results/durable-rejection-02'; runtime = r / 'runtime'
    plan = read(r / 'plan.json'); endpoint = read(r / 'endpoint.json')
    for n, h in plan['sources'].items(): assert sha(HERE / n) == h, n
    for n, h in read(runtime / 'sources.json').items(): assert sha(HERE.parent / n) == h, n
    events = [json.loads(l) for l in (runtime / 'events.jsonl').read_text().splitlines()]
    assert (runtime / 'events.jsonl').read_bytes() == (runtime / 'delivered.jsonl').read_bytes()
    parent = read(r / 'parent-calls.json'); state = start(endpoint['socket'])
    def advance_call(state, call):
        q, a = call['request'], call['reply']
        assert q['after'] == state['cursor'] and a['records'] == events[q['after']:a['cursor']]
        return advance(state, endpoint['socket'], q['after'], a)
    for call in parent[:-1]:
        state = advance_call(state, call); assert state == call['continuation']
    crashed = read(r / 'after-crash.json'); loss = read(r / 'loss.json'); sent = read(r / 'crash-request.json')
    assert state == read(r / 'before-loss.json') == crashed['continuation']
    assert crashed['pending']['request'] == sent and crashed['pending']['write_state'] == 'may_have_been_sent'
    assert hashlib.sha256((json.dumps(sent) + '\n').encode()).hexdigest() == loss['request_sha256']
    assert loss['received_response_bytes'] == 0 and loss['server_receipt_at_exit'] == 'unknown'
    processes = read(r / 'processes.json')
    assert [x['mode'] for x in processes] == ['crash', 'blocked', 'recover-0']
    assert [x['exit_code'] for x in processes] == [17, 0, 0]
    assert len({x['pid'] for x in processes}) == 3 and all(x['stderr'] == '' for x in processes)
    assert loss['worker_pid'] == processes[0]['pid']
    blocked = read(r / 'blocked.json'); assert blocked['pid'] == processes[1]['pid'] and blocked['transport_called'] is False
    assert not (r / 'blocked-request.json').exists()
    recovery = read(r / 'recover-0-result.json')
    assert recovery['worker_pid'] == processes[2]['pid']
    call = recovery['result']; assert 'command' not in call['request']
    state = advance_call(state, call); assert state == call['state']['continuation']
    pending, resolution = reconcile(crashed['pending'], call['reply']['records'])
    assert pending is None and resolution == call['state']['last_resolution']
    assert call['state'] == read(r / 'recovered.json') == read(r / 'journal.json')
    aid, rid = sent['command']['id'], sent['request_id']
    assert [e['id'] for e in events if e['event'] == 'accepted'] == ['select']
    echoes = [e for e in events if e['event'] == 'command' and e['command'].get('transport_request_id') == rid]
    assert len(echoes) == 1 and echoes[0]['command'] == dict(sent['command'], transport_request_id=rid)
    assert sum(s == {'op': 'chord', 'modifier': 'Control_L', 'key': 's'} for s in sent['command']['steps']) == 1
    terms = [e for e in events if e['event'] == 'terminal']
    assert len(terms) == 1 and all(e['status'] == 'completed' and e['release']['verified'] is True
                                 and e['release']['keys_down'] == [] and e['release']['buttons_down'] == [] for e in terms)
    rejects = [e for e in events if e['event'] == 'rejected']
    assert len(rejects) == 1 and rejects[0] == resolution['rejected']
    assert not any(e['event'] == 'step_started' and e.get('id') == aid for e in events)
    assert parent[-1]['request']['command']['op'] == 'finish'
    state = advance_call(state, parent[-1]); assert state == parent[-1]['continuation']
    lives = read(r / 'live-checks.json'); assert len(lives) == 4
    assert len({l['bridge_pid'] for l in lives}) == 1 and all(l['poll'] is None for l in lives)
    assert lives[1]['checked_ns'] >= processes[0]['ended_ns']
    assert lives[-1]['checked_ns'] >= processes[-1]['ended_ns']
    decoder = Decoder('live-control'); observations = [e for e in events if e['event'] == 'observation']
    assert len(observations) == 3
    for n, e in enumerate(observations, 1):
        frame = decoder.accept((runtime / f'{n:03d}.ait').read_bytes())
        with Image.open(runtime / Path(e['image']).name) as im:
            assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
    rect = ET.parse(runtime / 'shape.svg').getroot().find('.//{http://www.w3.org/2000/svg}rect')
    values = {k: float(rect.get(k)) for k in ('x', 'y', 'width', 'height')}
    assert values == plan['expected_svg'] and rect.get('transform') is None
    assert read(r / 'result.json')['exit_code'] == 0
    assert not Path(endpoint['socket']).exists() and not Path(endpoint['cancel_socket']).exists()
    report = {'events': len(events), 'frames_exact': len(observations), 'distinct_workers': 3,
              'input_submission_after_loss': 0, 'recovery_reads': 1, 'saved_svg': values, 'svg_sha256': sha(runtime / 'shape.svg'),
              'send_to_recovery_process_exit_ms': (processes[-1]['ended_ns'] - loss['send_completed_ns']) / 1e6,
              'recovery_process_wall_ms': (processes[-1]['ended_ns'] - processes[-1]['started_ns']) / 1e6,
              'scope': 'expired submit rejected before admission; actual socket process exit/recovery, no new model input',
              'audit_sha256': sha(Path(__file__))}
    (r / 'audit.json').write_text(json.dumps(report, indent=2) + '\n'); print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
