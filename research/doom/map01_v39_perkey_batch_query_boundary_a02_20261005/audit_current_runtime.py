#!/usr/bin/env python3
"""Verify V39 session selection and owner-source distinction at the pinned main."""
import ast,hashlib,json,subprocess
from pathlib import Path
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
lock=json.loads((HERE/'CURRENT_RUNTIME_SOURCE_LOCK.json').read_text(encoding='utf-8'))
base=lock['delivery_base_main']
texts={}
for path,expected in lock['files'].items():
    raw=subprocess.check_output(['git','show',f'{base}:{path}'],cwd=ROOT)
    assert hashlib.sha256(raw).hexdigest()==expected['sha256'],path
    assert subprocess.check_output(['git','rev-parse',f'{base}:{path}'],cwd=ROOT,text=True).strip()==expected['git_blob'],path
    texts[path]=raw.decode('utf-8')
controller=texts['research/doom/map01_overlap_controller_v39.py']
assert 'session_map01_v15.py' in controller and 'measurement_session' in controller
assert 'session_map01_v12.py' in controller
session12=texts['research/doom/session_map01_v12.py']
assert 'sys.path.insert(0, str(HERE.parent / "live_control"))' in session12
assert 'from doom_typed_release_backend_v1 import Backend' in session12
assert 'from executor_v12 import Executor' in session12
session15=texts['research/doom/session_map01_v15.py']
assert 'from executor_v13 import Executor as ReleaseOrderedExecutor' in session15
assert 'from doom_owner_thread_release_batch_backend_v1 import Backend as TelemetryBackend' in session15
assert 'base.Backend=TelemetryBackend;base.Executor=ReleaseOrderedExecutor' in session15
backend=texts['research/doom/doom_owner_thread_release_batch_backend_v1.py']
assert 'from input_transition_owner_v4 import InputOwner' in backend
assert 'self.owner.call("up", self.lease, key)' in backend
assert 'self.owner.call("input_state")' in backend
transition=texts['research/live_control/input_transition_owner_v4.py']
assert 'from input_owner_v12 import InputOwner as OwnerWithKeyUpReceipt' in transition
assert 'super().call(operation, lease, key)' in transition
runtime_owner=texts['research/live_control/input_owner_v12.py']
assert 'event=\'owner_explicit_keyup\'' in runtime_owner
assert 'physical_verification_authoritative=False' in runtime_owner
assert 'sample_key_state' not in runtime_owner and '_classify_release' not in runtime_owner
assert runtime_owner.count('d.query_keymap()')==1
assert 'owned_keycodes=sorted(held)' in runtime_owner
experiment_owner=(HERE/'input_owner_v12.py').read_text(encoding='utf-8')
assert 'def _classify_release' in experiment_owner and 'sample_key_state' in experiment_owner
assert hashlib.sha256(experiment_owner.encode()).hexdigest()==lock['files'][lock['selection']['experiment_classifier_snapshot']]['sha256']
print(json.dumps({'status':'CURRENT_RUNTIME_SELECTION_PASS','default':'session_map01_v12 -> Backend v1 / InputOwner v10','opt_in':'session_map01_v15 -> release-batch Backend v1 -> transition owner v4 -> live_control/input_owner_v12','runtime_up':'XTest KeyRelease + XSync receipt; no per-key keymap classification; aggregate owner-state reconciliation after batch','experiment_source_matches_runtime':False},sort_keys=True))
