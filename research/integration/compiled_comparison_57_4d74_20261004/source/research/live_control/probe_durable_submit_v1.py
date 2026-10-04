"""Separate-process crash/resume with injected archived runtime replies, no GUI input."""
import copy, hashlib, json, os, subprocess, sys
from pathlib import Path
from durable_submit_v1 import initialize, run, reconcile, locked

HERE = Path(__file__).resolve().parent


def dump(path, value): path.write_text(json.dumps(value, indent=2) + '\n')


def worker(root, mode):
    journal = root / 'journal.json'
    def transport(socket, request, **kwargs):
        dump(root / (mode + '-request.json'), request)
        if mode == 'crash': os._exit(17)
        if mode == 'blocked': raise AssertionError('blocked call reached transport')
        if 'command' in request: raise AssertionError('recovery attempted command')
        return json.loads((root / (mode + '-reply.json')).read_text())
    spec = {'events': ['terminal'], 'timeout': 0}
    if mode in ('crash', 'blocked'):
        spec['command'] = {'op': 'submit', 'expected_sequence': 3,
                           'valid_until_ns': 36700470038, 'steps': [{'op': 'observe'}]}
    try:
        result = run(journal, spec, transport)
    except ValueError as error:
        if mode != 'blocked' or str(error) != 'unresolved command; read only': raise
        dump(root / 'blocked.json', {'refused': str(error), 'pid': os.getpid()})
    else: dump(root / (mode + '-result.json'), result)


def main():
    root = HERE / 'results/durable-submit-01'
    root.mkdir(exist_ok=False)
    source = HERE / 'results/inkscape-lost-reply-01'
    dump(root / 'plan.json', {'scope': 'Linux separate-process crash before transport; injected archived replies with generated identities, no live GUI/network',
         'sources': {name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                     for name in ['durable_submit_v1.py', 'probe_durable_submit_v1.py', 'received_continuation_v1.py', 'unix_json_deadline.py']},
         'archive_sha256': hashlib.sha256((source / 'runtime/events.jsonl').read_bytes()).hexdigest()})
    checkpoint = json.loads((source / 'before-loss.json').read_text())
    journal = root / 'journal.json'
    initialize(journal, checkpoint)
    outcomes = []
    def child(mode, code=0):
        p = subprocess.run([sys.executable, __file__, str(root), mode], capture_output=True, text=True, timeout=10)
        outcomes.append({'mode': mode, 'exit_code': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
        dump(root / 'processes.json', outcomes)
        assert p.returncode == code, outcomes[-1]
    child('crash', 17)
    crashed = json.loads(journal.read_text())
    dump(root / 'after-crash.json', crashed)
    assert crashed['pending']['write_state'] == 'may_have_been_sent'
    assert crashed['continuation'] == checkpoint
    child('blocked')
    assert not (root / 'blocked-request.json').exists()
    assert json.loads(journal.read_text()) == crashed
    records = [json.loads(line) for line in (source / 'runtime/events.jsonl').read_text().splitlines()][17:47]
    # Archived evidence is deliberately rebound to the generated test identity.
    q = crashed['pending']['request']
    records[0]['command'] = dict(q['command'], transport_request_id=q['request_id'])
    for e in records[1:]:
        if e.get('id') == 'move-save': e['id'] = q['command']['id']
    dump(root / 'accepted-reply.json', {'status': 'timeout', 'cursor': 19, 'records': records[:2]})
    child('accepted')
    accepted = json.loads(journal.read_text())
    assert accepted['pending']['echo_seen'] and accepted['pending']['accepted']
    child('blocked')
    assert json.loads(journal.read_text()) == accepted
    dump(root / 'terminal-reply.json', {'status': 'boundary', 'cursor': 47, 'records': records[2:]})
    child('terminal')
    finished = json.loads(journal.read_text())
    assert finished['pending'] is None
    assert finished['last_resolution']['terminal']['release']['verified'] is True
    assert finished['continuation']['cursor'] == 47
    # Negative controls target admission/release/attribution, not only serialization.
    pending = crashed['pending']
    terminal = records[-1]
    assert terminal['event'] == 'terminal'
    controls = {}
    cases = {'terminal_without_echo': [terminal], 'echo_without_admission': [records[0], terminal],
             'foreign_command': [records[0], {'event': 'command', 'command': {'op': 'clock'}}, records[1], terminal]}
    held = copy.deepcopy(terminal); held['release']['buttons_down'] = [1]
    cases['held_input'] = [records[0], records[1], held]
    for name, events in cases.items():
        remaining, resolution = reconcile(pending, events)
        assert remaining is not None and resolution is None
        controls[name] = 'remains unresolved'
    # A competing process cannot enter transport while the journal owner is active.
    with locked(journal):
        p = subprocess.run([sys.executable, __file__, str(root), 'terminal'], capture_output=True, text=True, timeout=10)
        assert p.returncode != 0 and 'BlockingIOError' in p.stderr
        dump(root / 'lock-contention.json', {'exit_code': p.returncode, 'stderr': p.stderr})
    assert json.loads(journal.read_text()) == finished
    dump(root / 'result.json', {'controls': controls, 'separate_processes': len(outcomes),
         'crash_exit': 17, 'transport_calls_while_blocked': 0, 'authority': 'none',
         'limitations': ['injected replies', 'crash before any real send', 'not power-loss/filesystem fault test', 'no runtime restart or task success proof']})
    print(json.dumps({'processes': len(outcomes), 'controls': controls, 'result': str(root)}))


if __name__ == '__main__':
    if len(sys.argv) == 3: worker(Path(sys.argv[1]), sys.argv[2])
    else: main()
