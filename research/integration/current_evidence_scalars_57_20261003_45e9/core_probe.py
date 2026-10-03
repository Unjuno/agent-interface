"""Replay the fixed discovery controls on either exact baseline or repaired core."""
import importlib.machinery
import importlib.util
import hashlib
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
loader = importlib.machinery.SourceFileLoader('_probe_core', str(path))
spec = importlib.util.spec_from_loader('_probe_core', loader)
core = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = core
loader.exec_module(core)
program = {'schema': 'agent-interface/program-v1', 'program_id': 'scalar-probe',
           'source': {'observation_seq': 1, 'binding_revision': 1},
           'authority': {'lease_id': 'test-only', 'expires_at_ns': 100},
           'terminal': {'release_all_required': True}, 'ops': [{'op': 'release_all'}]}
manifest = core.capability_manifest('no-device', 'linux', 'no-device', core.KNOWN_CAPABILITIES)
cases = [('valid', {}), ('expired', {'now_ns': 101}), ('clock_nan', {'now_ns': float('nan')}),
         ('clock_negative', {'now_ns': -1}), ('clock_bool', {'now_ns': True}),
         ('sequence_bool', {'current_observation_seq': True}),
         ('sequence_float', {'current_observation_seq': 1.0}),
         ('revision_bool', {'current_binding_revision': True}),
         ('revision_float', {'current_binding_revision': 1.0})]
rows = []
for label, changes in cases:
    result = core.admit_program(program, manifest,
                               **dict(dict(now_ns=99, current_observation_seq=1,
                                           current_binding_revision=1), **changes))
    rows.append(dict(case=label, changed={k: {'type': type(v).__name__, 'repr': repr(v)}
                                         for k,v in changes.items()},
                     accepted=result.accepted, error=result.error))
print(json.dumps({'scope': 'input-free host engineering reproduction; no backend constructed',
                  'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'rows': rows}, indent=2, allow_nan=False))
