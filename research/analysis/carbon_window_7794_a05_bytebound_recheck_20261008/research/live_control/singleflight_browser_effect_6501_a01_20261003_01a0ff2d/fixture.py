"""Owned loopback form and independent effect/read ledger; no browser imports."""
import html
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class Fixture:
    def __init__(self, fixtures):
        self.fixtures = fixtures
        self.lock = threading.Lock()
        self.serial = threading.Lock()
        self.release = threading.Event()
        self.rows = []
        self.current = None
        self.active = 0
        self.next_id = 0
    def emit(self, event, **fields):
        row = {'seq': len(self.rows), 'ns': time.perf_counter_ns(), 'event': event, **fields}
        self.rows.append(row)
        return row
    def setup(self, case_id, policy):
        case = next(c for c in self.fixtures['cases'] if c['id'] == case_id)
        with self.lock:
            if self.active:
                raise RuntimeError('previous read still active')
            if self.current is not None:
                self.close_case_unlocked()
            self.current = {'case': case, 'policy': policy, 'generation': 1, 'commits': {}, 'reads': 0}
            self.release.clear()
            self.emit('setup', case=case_id, policy=policy)
    def close_case_unlocked(self):
        self.emit('case_closed', case=self.current['case']['id'],policy=self.current['policy'],
                  generation=self.current['generation'],commits=dict(self.current['commits']),
                  reads=self.current['reads'],active_reads=self.active)
    def close_case(self):
        with self.lock:
            if self.current is not None:
                self.close_case_unlocked()
                self.current = None
    def scope(self, target, generation):
        case = self.current['case']['id']
        return {'verifier':'dom-ready-v1','source':case,'target':target,'generation':generation,
                'digest':f'{case}/{target}/{generation}/READY','predicate':'ready',
                'window':case,'role':'read_only'}
    def read(self, payload):
        with self.lock:
            self.active += 1
            self.next_id += 1
            rid = self.next_id
            # Capture at request arrival. Queuing must not silently refresh old scope.
            scope = self.scope(payload['target'], self.current['generation'])
            self.current['reads'] += 1
            self.emit('read_arrived', read_id=rid, phase=payload['phase'], scope=scope,
                      dom_snapshot=payload['snapshot'])
        try:
            with self.serial:
                with self.lock:
                    self.emit('read_service_begin', read_id=rid)
                if payload['phase'] == 'offered' and not self.release.wait(10):
                    raise TimeoutError('fixture release barrier missing')
                time.sleep(self.fixtures['service_delay_ms']/1000)
                result = {'read_id':rid, 'scope':scope,'value':'READY','evidence_ref':f'read-{rid}'}
                with self.lock:
                    self.emit('read_return', **result)
                return result
        finally:
            with self.lock:
                self.active -= 1
    def flip(self):
        with self.lock:
            self.current['generation'] += 1
            self.emit('generation_flip', generation=self.current['generation'])
            return {'generation': self.current['generation']}
    def commit(self, payload):
        with self.lock:
            case = self.current['case']
            rid, target, generation = payload['request_id'], payload['target'], payload['generation']
            wanted = case['targets'].get(rid)
            accepted = (wanted == target and type(generation) is int and
                        generation == self.current['generation'] and rid not in self.current['commits'] and
                        payload['intent'] == f"{case['id']}/{rid}/{wanted}")
            if accepted:
                self.current['commits'][rid] = target
            self.emit('commit', request_id=rid, target=target, generation=generation,
                      intent=payload['intent'], evidence_ref=payload['evidence_ref'], accepted=accepted)
            return {'accepted':accepted,'request_id':rid,'target':target,
                    'count':len(self.current['commits'])}
    def page(self):
        with self.lock:
            case = self.current['case']
            generation = self.current['generation']
            forms = ''.join(f'''<section><h2>Request {rid} → {target}</h2>
<input id="evidence-{rid}" aria-label="Verification reference for {rid}">
<button id="commit-{rid}" data-request="{rid}" data-target="{target}" data-intent="{case['id']}/{rid}/{target}">Commit {rid} to {target}</button>
<output id="result-{rid}">Pending</output></section>''' for rid,target in case['targets'].items())
            return f'''<!doctype html><html><meta charset="utf-8"><title>Private verification fixture</title>
<style>body{{font:18px system-ui;margin:24px;background:#f5f7fb;color:#17243c}}section{{background:white;padding:12px;margin:12px 0}}button{{padding:8px}}input{{padding:8px}}output{{display:block;margin:8px}}</style>
<h1>Private verification fixture</h1><p id="source" data-source="{case['id']}">{case['id']} · generation <span id="generation">{generation}</span></p>
<div id="target-A" data-target="A" data-generation="{generation}">A: READY</div>
<div id="target-B" data-target="B" data-generation="{generation}">B: READY</div>
<button id="flip">Change generation</button>{forms}
<script>
document.querySelector('#flip').onclick=async()=>{{let v=await(await fetch('/flip',{{method:'POST'}})).json();document.querySelector('#generation').textContent=v.generation;for(let t of ['A','B'])document.querySelector('#target-'+t).dataset.generation=v.generation;}};
for(let b of document.querySelectorAll('[id^="commit-"]'))b.onclick=async()=>{{let r=b.dataset.request;let payload={{request_id:r,target:b.dataset.target,intent:b.dataset.intent,generation:Number(document.querySelector('#target-'+b.dataset.target).dataset.generation),evidence_ref:document.querySelector('#evidence-'+r).value}};let v=await(await fetch('/commit',{{method:'POST',headers:{{'Content-Type':'application/json'}},body:JSON.stringify(payload)}})).json();document.querySelector('#result-'+r).textContent=v.accepted?'Committed '+v.target:'Refused';}};
</script></html>'''.encode()

def serve(fixture):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass
        def respond(self, value, status=200, content_type='application/json'):
            data = value if type(value) is bytes else json.dumps(value).encode()
            self.send_response(status)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        def do_GET(self):
            if self.path == '/':
                self.respond(fixture.page(), content_type='text/html; charset=utf-8')
            elif self.path == '/barrier':
                with fixture.lock:
                    self.respond({'active':fixture.active,'reads':fixture.current['reads']})
            else:
                self.respond({'error':'unknown route'}, 404)
        def do_POST(self):
            try:
                payload = json.loads(self.rfile.read(int(self.headers.get('Content-Length','0'))) or b'{}')
                if self.path == '/setup':
                    fixture.setup(payload['case'], payload['policy']); self.respond({'ready':True})
                elif self.path == '/read':
                    self.respond(fixture.read(payload))
                elif self.path == '/release':
                    fixture.release.set(); self.respond({'released':True})
                elif self.path == '/flip':
                    self.respond(fixture.flip())
                elif self.path == '/commit':
                    self.respond(fixture.commit(payload))
                else:
                    self.respond({'error':'unknown route'}, 404)
            except Exception as error:
                self.respond({'error':type(error).__name__}, 500)
    server = ThreadingHTTPServer(('127.0.0.1',0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
