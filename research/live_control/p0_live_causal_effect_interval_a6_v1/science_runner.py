from __future__ import annotations
import hashlib, importlib.util, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BASE=REPO/'research/live_control/p0_live_causal_effect_x11_stackfile_a5_v1/science_runner.py'
TEMPORAL=HERE/'temporal_candidate.py'
BASE_BLOB='d8c509a55fe5363dc5211aebe510a720e964f7f3'
TEMPORAL_BLOB='8a44d0566701ee0cb5e7fadecbb7ee1f1a168a17'

def git_blob(path):
    b=Path(path).read_bytes()
    return hashlib.sha1(f'blob {len(b)}\0'.encode()+b).hexdigest()

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    m=importlib.util.module_from_spec(spec)
    sys.modules[name]=m
    spec.loader.exec_module(m)
    return m

if git_blob(BASE)!=BASE_BLOB:
    raise RuntimeError('base science source drift')
if git_blob(TEMPORAL)!=TEMPORAL_BLOB:
    raise RuntimeError('temporal candidate source drift')

_base=load('science_base_1340',BASE)

def source_gate(repo_root,tmp):
    deps=_base.source_gate(repo_root,tmp)
    temporal=Path(repo_root)/'research/live_control/p0_live_causal_effect_interval_a6_v1/temporal_candidate.py'
    if git_blob(temporal)!=TEMPORAL_BLOB:
        raise RuntimeError('temporal candidate checkout drift')
    deps=dict(deps)
    deps['temporal']=str(temporal)
    deps['temporal_blob']=TEMPORAL_BLOB
    deps['base_science_blob']=BASE_BLOB
    return deps

one_session=_base.one_session
summarize=_base.summarize
