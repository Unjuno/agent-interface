from __future__ import annotations
import hashlib, importlib.util, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
PARENT=REPO/'research/measurement/useful_effect_occupancy_interval_union_v1/parent_candidate.py'
INTERVAL=REPO/'research/measurement/useful_effect_occupancy_interval_union_v1/interval_candidate.py'
PARENT_BLOB='0482cf4c08b8c04d524a3eac11b798f07f0e0524'
INTERVAL_BLOB='289b58e1f0afeffbf453a4c577cf3f61c3013154'

def git_blob(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m

if git_blob(PARENT)!=PARENT_BLOB:
    raise RuntimeError('parent temporal source drift')
if git_blob(INTERVAL)!=INTERVAL_BLOB:
    raise RuntimeError('interval helper source drift')

_parent=load('temporal_parent_1340',PARENT)
_interval=load('temporal_interval_1340',INTERVAL)
_parent.occupancy_only=_interval.occupancy_interval_union

valid_id=_parent.valid_id
Interval=_parent.Interval
Actuation=_parent.Actuation
Event=_parent.Event
EffectRecord=_parent.EffectRecord
BUCKETS=_parent.BUCKETS
occupancy_only=_interval.occupancy_interval_union
analyze=_parent.analyze
