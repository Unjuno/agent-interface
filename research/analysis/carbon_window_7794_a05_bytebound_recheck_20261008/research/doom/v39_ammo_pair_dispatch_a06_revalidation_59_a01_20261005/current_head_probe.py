import ast, json, queue, time
from pathlib import Path

module = ast.parse(Path('controller.py').read_text(encoding='utf-8'))
wait_nodes = [n for n in ast.walk(module) if isinstance(n, ast.FunctionDef) and n.name == 'wait']
assert len(wait_nodes) == 1
monitor_node = next(n for n in module.body if isinstance(n, ast.ClassDef) and n.name == 'DoomCoverSignalPairMonitor')
helper_names = ('_typed_json_equal', '_signal_pair_matches', '_signal_pair_content_matches')
helpers = [next(n for n in module.body if isinstance(n, ast.FunctionDef) and n.name == name) for name in helper_names]
event_node = next(n for n in monitor_node.body if isinstance(n, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'event_types' for t in n.targets))
event_types = ast.literal_eval(event_node.value)
assert event_types == {'typed_observation', 'observation'}

class Process:
    def poll(self): return None
factory = ast.parse('''
def make_wait(rows):
    incoming = queue.Queue()
    process = Process()
    latest = None
    for row in rows:
        incoming.put(row)
''').body[0]
factory.body.extend([wait_nodes[0], ast.Return(value=ast.Name(id='wait', ctx=ast.Load()))])
factory_ns = {'queue': queue, 'time': time, 'Process': Process}
exec(compile(ast.fix_missing_locations(ast.Module(body=[factory], type_ignores=[])), '<frozen-wait>', 'exec'), factory_ns)
pair_ns = {}
exec(compile(ast.fix_missing_locations(ast.Module(body=[ast.Import(names=[ast.alias(name='time')]), *helpers, monitor_node], type_ignores=[])), '<frozen-monitor>', 'exec'), pair_ns)
Monitor = pair_ns['DoomCoverSignalPairMonitor']
BINDING = {'focus':7,'surface':9,'geometry':[0,0,640,480]}
def sig(name, value):
    return {'format':'observable-signal-v1','status':'observed','signal_id':name,
            'value':value,'sequence':11,'capture_ns':1_100_000_000,'binding':BINDING}
class Reader:
    def __init__(self, values, fail=False): self.values=values; self.fail=fail
    def read(self, row):
        if self.fail: raise OSError('frozen reader failure control')
        return self.values[row['sequence']]
class Guard:
    def __init__(self,name,value): self.name=name; self.spec={'source_sequence':10,'source_value':value}; self.source_capture_ns=1_000_000_000
    def evaluate(self,item):
        if self.name=='ammo' and item['value']==0:
            return {'status':'HARD_INVALIDATED','reason':'below_hard_minimum','requires_new_decision':True,'signal_id':self.name}
        soft=(self.name=='ammo' and item['value'] != 4)
        return {'status':'SOFT_CHANGED' if soft else 'UNCHANGED','reason':'within_validity_envelope','requires_new_decision':False,'signal_id':self.name}
def monitor(ammo_value=4, reader_fail=False):
    return Monitor({'health':Guard('health',100),'ammo':Guard('ammo',4)},
                   Reader({11:sig('health',100)}), Reader({11:sig('ammo',ammo_value)},reader_fail))
def full(ammo_value=0, frame='a'*64):
    return {'event':'observation','sequence':11,'capture_ns':1_100_000_000,'pointer_binding':BINDING,'frame_rgb_sha256':frame}
def typed(ammo_value=0, frame='a'*64):
    return {'event':'typed_observation','sequence':11,'capture_ns':1_100_000_000,'pointer_binding':BINDING,'frame_rgb_sha256':frame,'signals':{'health':sig('health',100),'ammo':sig('ammo',ammo_value)}}
def run(rows, mon, stop_event):
    wait=factory_ns['make_wait'](rows)
    r=wait(lambda x:x['event']==stop_event,timeout=0.2,observation_monitor=mon)
    return {'event':r['event'],'reason':r.get('invalidation',{}).get('reason'),
            'sequence':mon.last_sequence,'soft_event_count':mon.soft_event_count}

full_only=run([full(0)],monitor(0),'observation')
typed_full=run([typed(2),full(2)],monitor(2),'observation')
full_typed=run([full(2),typed(2)],monitor(2),'typed_observation')
reader_error=run([full(4)],monitor(4,reader_fail=True),'observation')
full_then_mismatched_typed=run([full(2),typed(3)],monitor(2),'typed_observation')
assert full_only == {'event':'policy_invalidation','reason':'ammo:below_hard_minimum','sequence':11,'soft_event_count':0}, full_only
assert typed_full == {'event':'observation','reason':None,'sequence':11,'soft_event_count':1}, typed_full
assert full_typed == {'event':'typed_observation','reason':None,'sequence':11,'soft_event_count':1}, full_typed
assert reader_error['event']=='policy_invalidation' and reader_error['reason']=='signal_pair_source_unavailable', reader_error
assert full_then_mismatched_typed['event']=='policy_invalidation' and full_then_mismatched_typed['reason']=='signal_pair_duplicate_epoch_mismatch', full_then_mismatched_typed
print(json.dumps({'disposition':'PASS_A06_CURRENT_HEAD_DISPATCH_AND_DEDUP_BOUNDARY',
 'source_event_types':sorted(event_types),'full_only_zero_ammo':full_only,
 'typed_then_full_duplicate':typed_full,'full_then_typed_duplicate':full_typed,
 'reader_error':reader_error,'same_epoch_mismatched_pair':full_then_mismatched_typed},sort_keys=True))
