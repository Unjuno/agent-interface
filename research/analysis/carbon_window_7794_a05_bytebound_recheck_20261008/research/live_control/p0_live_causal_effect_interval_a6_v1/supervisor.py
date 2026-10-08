from __future__ import annotations
import hashlib, importlib.util, sys
from pathlib import Path

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]
BASE=REPO/'research/live_control/p0_live_causal_effect_x11_stackfile_a5_v1/supervisor.py'
BASE_BLOB='3ef3f84702a239bb797b43d396235fafffa318d7'
SCIENCE=HERE/'science_runner.py'
SCIENCE_BLOB='041b7cf1caba64f2bd1eabeee27b50d8b2b1ab0f'
TASK='P0-LIVE-CAUSAL-EFFECT-INTERVAL-A6-20260918-001'
ISSUE=1340
BRANCH='research/p0-live-causal-effect-interval-a6-20260918-001'

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
    raise RuntimeError('base supervisor source drift')
if git_blob(SCIENCE)!=SCIENCE_BLOB:
    raise RuntimeError('science wrapper source drift')

_base=load('supervisor_base_1340',BASE)
_base.HERE=HERE
_base.TASK=TASK
_base.ISSUE=ISSUE
_base.BRANCH=BRANCH
_base.SCIENCE=SCIENCE
_base.SCIENCE_BLOB=SCIENCE_BLOB

if __name__=='__main__':
    _base.main()
