"""Run the exact frozen PR projector and one fail-closed identity candidate."""
import importlib.util
import json
import hashlib
from pathlib import Path

HERE = Path(__file__).resolve().parent

def load(name, path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module.input_edge_receipts

baseline=load('baseline_projection',HERE/'SOURCE/baseline_projection.py')
candidate=load('candidate_projection',HERE/'candidate_projection.py')
source=json.loads((HERE/'SOURCE/pair.json').read_text())

def classify(fn, events):
    values=fn(events)
    return values[0] if len(values)==1 else {'status':'unexpected_receipt_count','count':len(values)}

cases=[]
for name, mutate in (
    ('positive_exact_ids', lambda rows: None),
    ('top_level_owner_mismatch', lambda rows: rows[1].update(owner_id='foreign-owner')),
    ('nested_owner_mismatch', lambda rows: rows[1]['owner_thread_keyup_receipt'].update(owner_id='foreign-owner')),
    ('cross_layer_mismatch', lambda rows: (rows[1].update(owner_id='foreign-owner'), rows[1]['owner_thread_keyup_receipt'].update(owner_id='foreign-owner'))),
    ('partial_explicit_identity', lambda rows: rows[1]['owner_thread_keyup_receipt'].pop('owner_id')),
    ('legacy_all_ids_absent', lambda rows: (rows[0].pop('owner_id',None), rows[1].pop('owner_id',None), rows[1]['owner_thread_keyup_receipt'].pop('owner_id',None))),
):
    rows=json.loads(json.dumps(source)); mutate(rows)
    cases.append({'case':name,'baseline':classify(baseline,rows),'candidate':classify(candidate,rows)})
hashes = {}
for path in sorted((HERE/'SOURCE').glob('*')):
    if path.is_file(): hashes[path.relative_to(HERE).as_posix()]=hashlib.sha256(path.read_bytes()).hexdigest()
for name in ('candidate_projection.py','test_candidate.py'):
    path=HERE/name; hashes[name]=hashlib.sha256(path.read_bytes()).hexdigest()
print(json.dumps({'schema':'map01-v39-legacy-owner-identity-a01-raw-v1','source_sha256':hashes,'cases':cases},sort_keys=True))
