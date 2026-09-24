"""Fixed directed process allocation; refuses overwriting case or batch directories."""
import json, os, select, subprocess, sys, tempfile, time, traceback
from pathlib import Path
from wire import call, encoded

ROOT = Path(__file__).resolve().parent
SCENARIOS = ('NORMAL_ACK', 'RECEIVED_ACK_LOST', 'DATA_DROPPED', 'DATA_DELAYED', 'QUERY_REPLY_LOST', 'FOREIGN_QUERY_REPLY')
POLICIES = ('HOLD', 'QUERY_ABSENT', 'SEAL_ABSENT')


def readline(proc):
    if not select.select([proc.stdout], [], [], 4)[0]:
        raise TimeoutError('actor response timeout')
    raw = proc.stdout.readline()
    if not raw:
        raise EOFError('actor stdout closed')
    return json.loads(raw)


def case(out, scenario, policy, ident):
    out.mkdir(parents=True, exist_ok=False)
    actors, streams, dialogue = {}, {}, []
    result = dict(id=ident, scenario=scenario, policy=policy, complete=False,
                  parent_pid=os.getpid(), start_ns=time.monotonic_ns(), processes={})
    with tempfile.TemporaryDirectory(prefix='r6k2-') as td:
        sink, relay = str(Path(td)/'sink'), str(Path(td)/'relay')
        def spawn(role, args):
            stderr = (out/(role+'.stderr')).open('xb')
            streams[role] = stderr
            argv = [sys.executable, '-S', '-B', str(ROOT/'actors.py'), role, *args]
            proc = subprocess.Popen(argv, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=stderr)
            actors[role] = proc
            result['processes'][role] = dict(pid=proc.pid, argv=argv)
            result['processes'][role]['ready'] = readline(proc)
            return proc
        def ask(req):
            p = actors['sender']
            p.stdin.write(encoded(req)); p.stdin.flush()
            reply = readline(p)
            dialogue.append(dict(request=req, response=reply))
            return reply
        try:
            spawn('receiver', [sink, '', ident, str(out/'receiver.jsonl')])
            spawn('relay', [relay, sink, ident, str(out/'relay.jsonl')])
            spawn('sender', [policy, relay, ident, str(out/'sender.jsonl')])
            delayed = []
            for rid in ('c1', 'c2'):
                assert ask({'op': 'PREPARE', 'id': rid, 'origin': 'CUE'})['accepted']
                ack = None
                if scenario in ('NORMAL_ACK', 'RECEIVED_ACK_LOST'):
                    ack = call(relay, {'op': 'RELEASE', 'id': rid, 'expose': scenario == 'NORMAL_ACK'})
                elif scenario == 'DATA_DROPPED':
                    call(relay, {'op': 'DROP', 'id': rid})
                else:
                    delayed.append(rid)
                ask({'op': 'ACK', 'id': rid, 'reply': ack})
            fault = {'QUERY_REPLY_LOST': 'LOST', 'FOREIGN_QUERY_REPLY': 'FOREIGN'}.get(scenario, 'NONE')
            for _ in range(2):
                ask({'op': 'RECONCILE', 'fault': fault})
            for rid, origin in (('c3', 'CUE'), ('a1', 'AUTO'), ('a2', 'AUTO')):
                response = ask({'op': 'PREPARE', 'id': rid, 'origin': origin})
                if response['accepted']:
                    ack = call(relay, {'op': 'RELEASE', 'id': rid, 'expose': True})
                    ask({'op': 'ACK', 'id': rid, 'reply': ack})
            for rid in delayed:
                call(relay, {'op': 'RELEASE', 'id': rid, 'expose': False})
            ask({'op': 'STOP'})
            call(relay, {'op': 'STOP'}); call(sink, {'op': 'STOP'})
            for role, proc in actors.items():
                result['processes'][role]['exit'] = proc.wait(timeout=4)
                if proc.returncode != 0:
                    raise RuntimeError('actor failed: '+role)
            result['complete'] = True
        except Exception:
            result['error'] = traceback.format_exc()
        finally:
            for role, proc in actors.items():
                if proc.poll() is None:
                    proc.terminate()
                result['processes'][role]['exit'] = proc.wait(timeout=4)
                proc.stdin.close(); proc.stdout.close(); streams[role].close()
            result['socket_cleanup'] = not Path(sink).exists() and not Path(relay).exists()
            result['end_ns'] = time.monotonic_ns()
            (out/'dialogue.json').write_bytes(encoded(dialogue))
            (out/'case.json').write_bytes(encoded(result))
    if not result['complete']:
        raise RuntimeError('incomplete case; preserve and stop')


def batch(phase, index):
    if phase not in ('construction2', 'formal') or index not in range(6):
        raise ValueError('phase/index')
    out = ROOT/phase/('b'+str(index))
    out.mkdir(parents=True, exist_ok=False)
    start = time.monotonic_ns()
    ids = []
    for rep in range(2):
        order = POLICIES if rep == 0 else POLICIES[::-1]
        for policy in order:
            ident = 'r6k2-'+phase+'-'+str(index)+'-'+str(rep)+'-'+policy
            case(out/ident, SCENARIOS[index], policy, ident)
            ids.append(ident)
    (out/'batch.json').write_bytes(encoded(dict(phase=phase,index=index,ids=ids,
       start_ns=start,end_ns=time.monotonic_ns(),complete=True,pid=os.getpid())))
    print(json.dumps({'index':index,'cases':len(ids),'complete':True}))


if __name__ == '__main__':
    batch(sys.argv[1], int(sys.argv[2]))
