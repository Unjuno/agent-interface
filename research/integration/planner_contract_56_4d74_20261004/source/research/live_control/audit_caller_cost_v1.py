"""Audit fixed workload then report descriptive caller/transport timing, no speed claim."""
import hashlib, json, statistics, sys, xml.etree.ElementTree as ET
from pathlib import Path
from PIL import Image
from received_continuation_v1 import start, advance
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'observation_tiles'))
from tile_transport import Decoder


def read(p): return json.loads(p.read_text())
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def describe(values):
    return {'n': len(values), 'median_ms': statistics.median(values), 'mean_ms': statistics.mean(values),
            'min_ms': min(values), 'max_ms': max(values)}


def main():
    root = HERE / 'results/caller-cost-01'; plan = read(root / 'plan.json')
    for n, h in plan['sources'].items(): assert sha(HERE / n) == h, n
    rows = []; summaries = []
    for index, mode in enumerate(plan['order']):
        out = root / f'{index+1:02d}-{mode}'; runtime = out / 'runtime'
        ep = read(out / 'endpoint.json'); events = [json.loads(l) for l in (runtime / 'events.jsonl').read_text().splitlines()]
        for n, h in read(runtime / 'sources.json').items(): assert sha(HERE.parent / n) == h, n
        calls = read(out / 'calls.json'); assert len(calls) == 8
        assert [c['operation'] for c in calls] == ['clock', 'submit'] * 4
        state = start(ep['socket'])
        def replay(call):
            nonlocal state
            q, a = call['request'], call['reply']
            assert q['after'] == state['cursor'] and a['records'] == events[q['after']:a['cursor']]
            state = advance(state, ep['socket'], q['after'], a)
            expected = call['state']['continuation'] if 'state' in call else call['continuation']
            assert state == expected
        replay(read(out / 'initial.json'))
        request_ids = []
        for cycle, measured in enumerate(calls):
            c = measured['result']; replay(c)
            q = c['request']; request_ids.append(q['request_id'])
            if mode == 'durable': assert c['state']['pending'] is None
            if measured['operation'] == 'clock':
                clock = state['clocks'][q['request_id']]['record']
            else:
                command = q['command']
                assert command['steps'] == [{'op': 'observe'}]
                assert command['expected_sequence'] == clock['sequence']
                assert command['valid_until_ns'] == clock['runtime_ns'] + 30_000_000_000
            b, e = measured['begin_ns'], measured['end_ns']
            nb, ne = measured['transport']['begin_ns'], measured['transport']['end_ns']
            assert b <= nb <= ne <= e
            row = {'session': index+1, 'mode': mode, 'operation': measured['operation'], 'cycle': cycle//2+1,
                   'total_ms': (e-b)/1e6, 'transport_ms': (ne-nb)/1e6,
                   'caller_outside_transport_ms': ((e-b)-(ne-nb))/1e6,
                   'before_transport_ms': (nb-b)/1e6, 'after_transport_ms': (e-ne)/1e6,
                   'journal_bytes': measured['journal_bytes'], 'cursor': state['cursor']}
            if measured['operation'] == 'submit':
                record = next(x for x in c['reply']['records'] if x['event'] == 'observation')
                assert b <= record['image_ready_ns'] <= e
                row['call_to_runtime_image_ready_ms'] = (record['image_ready_ns']-b)/1e6
                row['image_reused'] = record['image_reused']
            rows.append(row)
        assert len(set(request_ids)) == 8
        if mode == 'durable': assert read(out / 'journal.json') == calls[-1]['result']['state']
        replay(read(out / 'finish.json'))
        assert len([x for x in events if x['event'] == 'accepted']) == 4
        terms = [x for x in events if x['event'] == 'terminal']
        assert len(terms) == 4 and all(t['status'] == 'completed' and t['release']['verified'] is True for t in terms)
        assert not any(x['event'] == 'rejected' for x in events)
        obs = [x for x in events if x['event'] == 'observation']; assert len(obs) == 5
        decoder = Decoder('live-control')
        for n, record in enumerate(obs, 1):
            frame = decoder.accept((runtime / f'{n:03d}.ait').read_bytes())
            with Image.open(runtime / Path(record['image']).name) as im:
                assert (im.width, im.height, im.mode, im.tobytes()) == (frame.width, frame.height, frame.mode, frame.pixels)
        rect = ET.parse(runtime / 'shape.svg').getroot().find('.//{http://www.w3.org/2000/svg}rect')
        assert [float(rect.get(k)) for k in ('x', 'y', 'width', 'height')] == [50,50,40,30]
        assert rect.get('transform') is None
        assert read(out / 'result.json')['exit_code'] == 0 and not Path(ep['socket']).exists() and not Path(ep['cancel_socket']).exists()
        session_rows = [x for x in rows if x['session'] == index+1]
        summaries.append({'session': index+1, 'mode': mode, 'events': len(events), 'frames': len(obs),
                          'total_measured_ms': sum(x['total_ms'] for x in session_rows),
                          'caller_outside_transport_ms': sum(x['caller_outside_transport_ms'] for x in session_rows)})
    groups = {}
    for mode in ('received','durable'):
        for op in ('clock','submit'):
            group = [r for r in rows if r['mode'] == mode and r['operation'] == op]
            groups[mode+'_'+op] = {metric: describe([r[metric] for r in group])
                                  for metric in ('total_ms','transport_ms','caller_outside_transport_ms','before_transport_ms','after_transport_ms')}
            if op == 'submit': groups[mode+'_'+op]['call_to_runtime_image_ready_ms'] = describe([r['call_to_runtime_image_ready_ms'] for r in group])
    report = {'groups': groups, 'sessions': summaries, 'measured_calls': len(rows),
              'scope': 'ABBA two fresh sessions per mode, four cycles each; observe-only static GUI, in-memory API versus fsync journal; no model; no equal durability claim',
              'audit_sha256': sha(Path(__file__))}
    (root / 'timings.json').write_text(json.dumps(rows, indent=2)+'\n')
    (root / 'audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'sessions': summaries, 'groups': {k: {m:v[m] for m in ('total_ms','caller_outside_transport_ms')} for k,v in groups.items()}}, indent=2))


if __name__ == '__main__': main()
