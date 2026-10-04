"""Real GUI/socket write followed by caller os._exit; another process reconciles."""
import hashlib, json, os, socket, subprocess, sys, time
from pathlib import Path
from durable_submit_v2 import initialize, run
from received_continuation_v1 import start
from received_exchange_v2 import request_once
from unix_json_deadline import exchange
HERE = Path(__file__).resolve().parent


def dump(path, value): path.write_text(json.dumps(value, indent=2) + '\n')


def worker(root, mode):
    journal = root / 'journal.json'
    spec = json.loads((root / 'submit-spec.json').read_text()) if mode in ('crash', 'blocked') else {'events': ['terminal'], 'timeout': 3}
    def transport(path, q, **kwargs):
        if mode == 'blocked': raise AssertionError('unresolved submit reached transport')
        dump(root / (mode + '-request.json'), q)
        if mode == 'crash':
            payload = (json.dumps(q) + '\n').encode()
            connection = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            connection.settimeout(3); connection.connect(path)
            connection.sendall(payload)
            dump(root / 'loss.json', {'worker_pid': os.getpid(), 'send_completed_ns': time.perf_counter_ns(),
                 'request_sha256': hashlib.sha256(payload).hexdigest(), 'received_response_bytes': 0,
                 'server_receipt_at_exit': 'unknown', 'failure': 'deliberate os._exit(17) after sendall, no recv'})
            os._exit(17)
        reply = exchange(path, q, **kwargs)
        dump(root / (mode + '-reply.json'), reply)
        return reply
    try: result = run(journal, spec, transport)
    except ValueError as error:
        if mode != 'blocked' or str(error) != 'unresolved command; read only': raise
        dump(root / 'blocked.json', {'pid': os.getpid(), 'refused': str(error), 'transport_called': False})
    else: dump(root / (mode + '-result.json'), {'worker_pid': os.getpid(), 'result': result})


def main():
    root = HERE / 'results/durable-rejection-02'; root.mkdir(exist_ok=False)
    names = ['probe_durable_rejection_v2.py', 'durable_submit_v2.py', 'received_continuation_v1.py', 'received_exchange_v2.py',
             'cause_servo_socket_v7.py', 'cause_servo_interactive_v5.py', 'stopped_socket_v2.py', 'stopped_cursor_v2.py', 'stopped_scope_v2.py', 'stopped_scope_v1.py', 'unix_json_deadline.py', 'rejection_identity_v1.py']
    dump(root / 'plan.json', {'scope': 'scripted actual GUI, deliberate caller process exit after socket write, new process read-only recovery of expired pre-admission request',
         'seed': 234, 'expected_svg': {'x': 50, 'y': 50, 'width': 40, 'height': 30},
         'sources': {n: hashlib.sha256((HERE / n).read_bytes()).hexdigest() for n in names}})
    p = subprocess.Popen([sys.executable, str(HERE / 'cause_servo_socket_v7.py'), 'inkscape', 'serve', '--',
                          '--app', 'inkscape', '--seed', '234', '--out', str(root / 'runtime')],
                         stdout=subprocess.PIPE, stderr=(root / 'stderr.txt').open('w'), text=True)
    calls = []; processes = []; lives = []
    try:
        endpoint = json.loads(p.stdout.readline()); dump(root / 'endpoint.json', endpoint)
        state = start(endpoint['socket'])
        def call(spec):
            nonlocal state
            r = request_once(endpoint['socket'], state, spec)
            calls.append(r); state = r['continuation']; dump(root / 'parent-calls.json', calls)
            return r
        def clock(identifier):
            r = call({'events': ['clock'], 'timeout': 2, 'command': {'op': 'clock'}, 'request_id': identifier})
            assert r['matched_clock'] is not None
            return r['matched_clock']['record']
        def live(stage):
            status = p.poll(); assert status is None
            lives.append({'stage': stage, 'bridge_pid': p.pid, 'poll': status, 'checked_ns': time.perf_counter_ns()})
            dump(root / 'live-checks.json', lives)
        def child(mode, expected=0):
            begin = time.perf_counter_ns()
            c = subprocess.Popen([sys.executable, __file__, str(root), mode], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = c.communicate(timeout=15)
            processes.append({'mode': mode, 'pid': c.pid, 'exit_code': c.returncode, 'started_ns': begin,
                              'ended_ns': time.perf_counter_ns(), 'stdout': stdout, 'stderr': stderr})
            dump(root / 'processes.json', processes)
            assert c.returncode == expected, processes[-1]
        call({'events': ['observation'], 'timeout': 30}); c = clock('clock-select')
        call({'events': ['terminal'], 'timeout': 3, 'action_id': 'select', 'request_id': 'select-once',
              'command': {'op': 'submit', 'id': 'select', 'expected_sequence': c['sequence'], 'valid_until_ns': c['runtime_ns'] + 30_000_000_000,
                          'steps': [{'op': 'pointer_click', 'x': 619, 'y': 391, 'duration_ms': 80}, {'op': 'observe'}]}})
        c = clock('clock-edit')
        initialize(root / 'journal.json', state); dump(root / 'before-loss.json', state)
        dump(root / 'submit-spec.json', {'events': ['terminal'], 'timeout': 3,
             'command': {'op': 'submit', 'expected_sequence': c['sequence'], 'valid_until_ns': 1,
                         'steps': [{'op': 'pointer_click', 'x': 550, 'y': 106, 'duration_ms': 80},
                                   {'op': 'chord', 'modifier': 'Control_L', 'key': 'a'}, {'op': 'text', 'text': '96'},
                                   {'op': 'key', 'key': 'Return'}, {'op': 'chord', 'modifier': 'Control_L', 'key': 's'}, {'op': 'observe'}]}})
        live('before-crash'); child('crash', 17); live('after-crash')
        crashed = json.loads((root / 'journal.json').read_text()); dump(root / 'after-crash.json', crashed)
        assert crashed['continuation'] == state and crashed['pending'] is not None
        child('blocked'); live('after-blocked')
        assert json.loads((root / 'journal.json').read_text()) == crashed
        for attempt in range(5):
            child('recover-' + str(attempt)); live('after-recover-' + str(attempt))
            recovered = json.loads((root / 'journal.json').read_text())
            if recovered['pending'] is None: break
        else: raise AssertionError('still unresolved after bounded reads; no resend')
        state = recovered['continuation']
        assert recovered['last_resolution']['rejected']['admission'] == 'not_admitted'
        dump(root / 'recovered.json', recovered)
        call({'events': ['independent_evaluation'], 'timeout': 3, 'command': {'op': 'finish'}, 'request_id': 'finish-once'})
        code = p.wait(timeout=10); assert code == 0
        dump(root / 'result.json', {'exit_code': code, 'worker_count': len(processes), 'recovery_reads': attempt + 1,
             'unique_worker_pids': len({x['pid'] for x in processes}),
             'scope': 'actual GUI/AF_UNIX; intentional process exit, no organic outage, no new model planning'})
        print(json.dumps({'exit_code': code, 'workers': len(processes), 'recovery_reads': attempt + 1}))
    finally:
        if p.poll() is None: p.terminate(); p.wait(timeout=10)


if __name__ == '__main__':
    if len(sys.argv) == 3: worker(Path(sys.argv[1]), sys.argv[2])
    else: main()
