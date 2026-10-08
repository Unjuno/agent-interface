from __future__ import annotations
import ast
import hashlib
import json
from pathlib import Path
import queue
import threading
import time

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / 'source' / 'map01_overlap_controller_v39.py'

class Process:
    def poll(self): return None

class PipelineQueue:
    def __init__(self): self.inner = queue.Queue()
    def qsize(self): return self.inner.qsize()
    def get_nowait(self): return self.inner.get_nowait()
    def get(self, timeout): return self.inner.get(timeout=timeout)
    def put(self, row): self.inner.put(row)

class Monitor:
    event_types = {'observation'}
    def __init__(self): self.seen=[]
    def observe(self, row):
        self.seen.append(row)
        if row.get('health') == 60:
            return {'reason':'health_below_authored_floor','sequence':row['sequence']}
        return None

def source_functions():
    tree=ast.parse(SOURCE.read_text(encoding='utf-8'))
    drain=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='drain_pending_observation_events')
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    wait=next(n for n in ast.walk(main) if isinstance(n,ast.FunctionDef) and n.name=='wait')
    drain_mod=ast.fix_missing_locations(ast.Module(body=[drain],type_ignores=[]))
    ns={'queue':queue}
    exec(compile(drain_mod,str(SOURCE),'exec'),ns)
    factory=ast.parse('def factory(process,incoming):\n latest=None\n').body[0]
    factory.body.append(wait)
    factory.body.extend(ast.parse('return wait, lambda: latest').body)
    factory_mod=ast.fix_missing_locations(ast.Module(body=[factory],type_ignores=[]))
    fns={'queue':queue,'time':time}
    exec(compile(factory_mod,str(SOURCE),'exec'),fns)
    return ns['drain_pending_observation_events'], fns['factory']

def run_scenario():
    drain,make_wait=source_functions()
    incoming=PipelineQueue(); process=Process(); wait,get_latest=make_wait(process,incoming)
    monitor=Monitor(); gate=threading.Event(); reader_started=threading.Event()
    observation={'event':'observation','sequence':42,'health':60,'capture_ns':123456}
    terminal={'event':'terminal','id':'cover-7','status':'cancelled',
              'release':{'verified':True,'keys_down':[],'buttons_down':[]}}
    def reader_pipeline():
        # Represents the stdout reader after decoding a line but before queue.put.
        reader_started.set()
        if not gate.wait(2): raise TimeoutError('test did not release reader')
        incoming.put(observation)
        incoming.put(terminal)
    reader=threading.Thread(target=reader_pipeline)
    reader.start(); assert reader_started.wait(1)
    result={'events':['planner_future_done','reader_holds_decoded_observation']}
    snapshot=drain(incoming,monitor,'cover-7')
    result['events'].append('bounded_snapshot_empty')
    assert snapshot=={'latest':None,'terminal':None,'invalidation':None},snapshot
    result['events'].append('executor_cancel_sent')
    gate.set()
    boundary=wait(lambda r:r.get('event')=='terminal' and r.get('id')=='cover-7',
                  timeout=2,observation_monitor=monitor)
    result['events'].append('wait_returns_policy_invalidation')
    assert boundary.get('event')=='policy_invalidation',boundary
    invalidation=boundary['invalidation']
    result['events'].append('planner_interrupt_after_completed_answer')
    terminal_boundary=wait(lambda r:r.get('event')=='terminal' and r.get('id')=='cover-7',timeout=2)
    assert terminal_boundary is terminal or terminal_boundary==terminal
    result['events'].append('matching_cover_terminal')
    answer_discarded=invalidation is not None
    result['events'].append('completed_answer_discarded' if answer_discarded else 'completed_answer_admitted')
    reader.join(2)
    assert not reader.is_alive()
    assert monitor.seen==[observation]
    assert get_latest()==observation
    assert terminal_boundary['release']=={'verified':True,'keys_down':[],'buttons_down':[]}
    assert answer_discarded
    result.update({'status':'PASS_INFLIGHT_OBSERVATION_INVALIDATES_BEFORE_TERMINAL',
        'snapshot_saw_event':False,'monitor_saw_event_after_snapshot':True,
        'invalidation':invalidation,'latest_sequence':get_latest()['sequence'],
        'terminal_release':terminal_boundary['release'],'answer_discarded':answer_discarded,
        'event_order_assumption':'observation line precedes matching terminal line on the same stdout stream',
        'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest()})
    return result

def main():
    result=run_scenario()
    (ROOT/'RESULT.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__': main()
