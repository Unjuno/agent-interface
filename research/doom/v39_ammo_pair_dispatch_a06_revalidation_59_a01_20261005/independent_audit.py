import ast, hashlib, json
from pathlib import Path
source=Path('controller.py').read_text(encoding='utf-8')
blob=hashlib.sha1((f'blob {len(source.encode())}\0').encode()+source.encode()).hexdigest()
assert blob=='d4f91d3102ef8124fdfbbd6374a3015c4e079a89',blob
mod=ast.parse(source)
monitor=next(n for n in mod.body if isinstance(n,ast.ClassDef) and n.name=='DoomCoverSignalPairMonitor')
event=next(n for n in monitor.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='event_types' for t in n.targets))
assert ast.literal_eval(event.value)=={'observation','typed_observation'}
observe=next(n for n in monitor.body if isinstance(n,ast.FunctionDef) and n.name=='observe')
assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='read' for n in ast.walk(observe))
assert any(isinstance(n,ast.FunctionDef) and n.name=='_signal_pair_content_matches' for n in mod.body)
rows=Path('test-output.txt').read_text(encoding='utf-8').splitlines()
payload=json.loads(next(x for x in reversed(rows) if x.startswith('{')))
assert payload['disposition']=='PASS_A06_CURRENT_HEAD_DISPATCH_AND_DEDUP_BOUNDARY'
assert payload['full_only_zero_ammo']['reason']=='ammo:below_hard_minimum'
assert payload['typed_then_full_duplicate']['soft_event_count']==1
assert payload['full_then_typed_duplicate']['soft_event_count']==1
assert payload['reader_error']['reason']=='signal_pair_source_unavailable'
assert payload['same_epoch_mismatched_pair']['reason']=='signal_pair_duplicate_epoch_mismatch'
print(json.dumps({'audit':'PASS_A06_PINNED_SOURCE_AND_PROBE_OUTPUT','controller_blob':blob,'cases':5,'frozen_suite_execution_count':0},sort_keys=True))
