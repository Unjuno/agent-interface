"""Ordinary new-input assay; never invokes historical formal runners."""
from __future__ import annotations
import copy
import hashlib
import json
import pathlib
import platform
import sys
import threading
import types

HERE = pathlib.Path(__file__).resolve().parent

def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()

def digest(value):
    return hashlib.sha256(encoded(value)).hexdigest()

def load_snapshot(name):
    path = HERE / 'sources' / (name + '.txt')
    module = types.ModuleType('retained_' + name.replace('.', '_'))
    module.__file__ = str(path)
    exec(compile(path.read_bytes(), str(path), 'exec'), module.__dict__)
    return module

def explicit_absence(case):
    """At the known first checkpoint, no delivered entry is unusable evidence."""
    result = copy.deepcopy(case)
    if result['checkpoint_events'] == []:
        result['checkpoint_events'] = [{'kind': 'MISSING'}]
    return result

def run():
    source_data = (HERE / 'SOURCE_MAP.json').read_bytes()
    sources = json.loads(source_data)
    for item in sources['sources'].values():
        data = (HERE / item['snapshot']).read_bytes()
        if hashlib.sha256(data).hexdigest() != item['sha256'] or len(data) != item['bytes']:
            raise ValueError('snapshot identity changed')
    candidate = load_snapshot('candidate.py')
    retained_auditor = load_snapshot('audit.py')
    case_data = (HERE / 'CASES.json').read_bytes()
    document = json.loads(case_data)
    rows = []
    owner = threading.get_ident()
    for item in document['cases']:
        if item['first_checkpoint_is_due'] is not True:
            raise ValueError('assay requires known first checkpoint')
        original = item['case']
        original_bytes = encoded(original)
        for arm in ['legacy', 'explicit_absence']:
            actual = copy.deepcopy(original) if arm == 'legacy' else explicit_absence(original)
            before = encoded(actual)
            output = candidate.evaluate(actual)
            certificate = retained_auditor.audit([actual], [output])
            rows.append({'case_id': original['id'], 'context': item['context'], 'encoding': item['encoding'], 'arm': arm, 'original_case_sha256': digest(original), 'evaluated_case': actual, 'evaluated_case_sha256': digest(actual), 'input_unchanged': encoded(actual) == before and encoded(original) == original_bytes, 'owner_thread_id': threading.get_ident(), 'output': output, 'retained_audit': certificate})
    return {'schema': 'checkpoint-delivery-raw-v1', 'kind': 'new ordinary known-checkpoint representation assay, not historical formal replay', 'source_map_sha256': hashlib.sha256(source_data).hexdigest(), 'cases_sha256': hashlib.sha256(case_data).hexdigest(), 'python': sys.version, 'platform': platform.platform(), 'owner_thread_id': owner, 'rows': rows}

if __name__ == '__main__':
    print(json.dumps(run(), sort_keys=True, indent=2))
