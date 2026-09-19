"""Fixed actual GUI observe workload, ABBA received/durable caller comparison."""
import hashlib, json, platform, subprocess, sys, time, uuid, tempfile, shutil
from pathlib import Path
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from durable_submit_v3 import initialize, run
from unix_json_deadline import exchange
HERE = Path(__file__).resolve().parent


def dump(path, value): path.write_text(json.dumps(value, indent=2) + '\n')


def main():
    root = HERE / 'results/journal-location-01'; root.mkdir(exist_ok=False)
    modes = ['mounted', 'native', 'native', 'mounted']
    names = ['probe_journal_location_v1.py', 'received_exchange_v2.py', 'received_continuation_v1.py', 'durable_submit_v3.py',
             'cause_servo_socket_v7.py', 'cause_servo_interactive_v5.py', 'stopped_socket_v2.py', 'stopped_cursor_v2.py',
             'stopped_scope_v2.py', 'unix_json_deadline.py']
    dump(root / 'plan.json', {'order': modes, 'seed': 236, 'cycles_per_session': 4, 'warmup_cycles': 0,
         'scope': 'same durable API and actual GUI workload; mounted versus native Linux journal; no model',
         'timer': 'same Linux perf_counter_ns around API call and transport callback; recording after stop',
         'excluded': ['runtime launch', 'initial observation', 'journal initialization', 'finish', 'result logging'],
         'sources': {n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in names},
         'environment': {'python': sys.version, 'platform': platform.platform(), 'journal_filesystem': 'WSL /mnt/c mounted Windows repository'}})
    for index, mode in enumerate(modes):
        out = root / f'{index+1:02d}-{mode}'; out.mkdir()
        p = subprocess.Popen([sys.executable, str(HERE / 'cause_servo_socket_v7.py'), 'inkscape', 'serve', '--',
                              '--app', 'inkscape', '--seed', '236', '--out', str(out / 'runtime')],
                             stdout=subprocess.PIPE, stderr=(out / 'stderr.txt').open('w'), text=True)
        calls = []; journal_home = None
        try:
            ep = json.loads(p.stdout.readline()); dump(out / 'endpoint.json', ep)
            initial = request_once(ep['socket'], start(ep['socket']), {'events': ['observation'], 'timeout': 30})
            state = initial['continuation']; dump(out / 'initial.json', initial)
            if mode == 'native': journal_home = tempfile.TemporaryDirectory(prefix='agent-interface-cost-')
            journal = (Path(journal_home.name) if journal_home else out) / 'journal.json'
            dump(out / 'journal-location.json', {'mode':mode,'path':str(journal),'native_temporary':journal_home is not None})
            if mode != 'received': initialize(journal, state)
            def timed(command, events):
                nonlocal state
                spec = {'command': command, 'events': events, 'timeout': 3}
                # Give both paths equivalent identity lengths and one request per operation.
                if mode == 'received':
                    spec['request_id'] = uuid.uuid4().hex
                    if command['op'] == 'submit':
                        command['id'] = 'durable-' + uuid.uuid4().hex
                        spec['action_id'] = command['id']
                network = []
                def measured(socket, q, **kwargs):
                    begin = time.perf_counter_ns()
                    reply = exchange(socket, q, **kwargs)
                    end = time.perf_counter_ns()
                    network.append({'begin_ns': begin, 'end_ns': end})
                    return reply
                begin = time.perf_counter_ns()
                result = run(journal, spec, measured) if mode != 'received' else request_once(ep['socket'], state, spec, measured)
                end = time.perf_counter_ns()
                assert len(network) == 1
                if mode != 'received':
                    assert result['state']['pending'] is None
                    state = result['state']['continuation']
                else: state = result['continuation']
                calls.append({'operation': command['op'], 'begin_ns': begin, 'end_ns': end, 'transport': network[0],
                              'result': result, 'journal_bytes': journal.stat().st_size if journal.exists() else 0})
                if command['op'] == 'clock':
                    clock = result['state']['last_resolution']['clock'] if mode != 'received' else result['matched_clock']['record']
                    assert state['clocks'][result['request']['request_id']]['record'] == clock
                    return clock
                terms = [e for e in result['reply']['records'] if e['event'] == 'terminal']
                assert len(terms) == 1 and terms[0]['status'] == 'completed'
            for cycle in range(4):
                c = timed({'op': 'clock'}, ['clock'])
                timed({'op': 'submit', 'expected_sequence': c['sequence'], 'valid_until_ns': c['runtime_ns'] + 30_000_000_000,
                       'steps': [{'op': 'observe'}]}, ['terminal'])
            dump(out / 'calls.json', calls)
            if journal_home: shutil.copy2(journal, out / 'journal.json')
            finish = request_once(ep['socket'], state, {'events': ['independent_evaluation'], 'timeout': 3,
                                    'command': {'op': 'finish'}, 'request_id': 'finish-once'})
            dump(out / 'finish.json', finish)
            code = p.wait(timeout=10); assert code == 0
            dump(out / 'result.json', {'mode': mode, 'exit_code': code, 'measured_calls': len(calls)})
            print(json.dumps({'session': index+1, 'mode': mode, 'calls': len(calls), 'exit_code': code}), flush=True)
        finally:
            if p.poll() is None: p.terminate(); p.wait(timeout=10)
            if journal_home: journal_home.cleanup()


if __name__ == '__main__': main()
