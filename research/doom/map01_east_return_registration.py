"""Construct a fixed registration for one isolated MAP01 east-return attempt.

This module builds data only; it never allocates a runtime or sends input.
"""
import re
from copy import deepcopy
from pathlib import Path
from map01_east_return_classification import SCOPED_RULES

PYTHON='/home/user/.cache/agent-interface-map01-20261103/bin/python'
CANDIDATE='/home/user/issue59-grandchild-bound-setup-yzkdlh9q/candidate/fixture.json'
MANIFEST='16f2bcf78b1d7739afd1fa0c141f1bbaee9dd2c9e3ff8e356ef3df743899d8d5'
SAVE='4e5b990cba8a86ca8a526ecdc59798c1869ea23c8f53468369e811f41d057ddc'
EVIDENCE='40ef78b09f62fcd1b66cc6dc08257aa7d9d3f75fa0fe0797160c3d8fd48b58dc'
IWAD='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
INITIAL_REFERENCE='c3f196d116c370b3d34daa47cafa73b400fd3fb8537b9c70d4a093b15a4b7988'
INITIAL_GUARD='8ec9b693c15fa881096f429b71333cbb93c107976ace02cbe5cb96eb35612afa'
EAST_REFERENCE='89a58ce4069bc4aff69805479164ed2cc9c96a61edb768a6685c1d6ad2fcc9cc'
UNIT_OPTIONS=['UMask=0077','PrivateTmp=yes','PrivateNetwork=yes','RuntimeMaxSec=60s','TimeoutStopSec=5s','KillMode=control-group']


def build_spec(root, unit, checkout, revision, tree, files, hashes):
    root=Path(root);checkout=Path(checkout)
    keys=('driver_sha256','launcher_sha256','preflight_sha256','auditor_sha256')
    if (not root.is_absolute() or not checkout.is_absolute() or type(unit) is not str
            or re.fullmatch(r'map01-east-[a-z0-9]+\.service',unit) is None
            or type(revision) is not str or re.fullmatch('[0-9a-f]{40}',revision) is None
            or type(tree) is not str or re.fullmatch('[0-9a-f]{40}',tree) is None
            or type(files) is not dict or type(hashes) is not dict
            or any(type(hashes.get(key)) is not str or re.fullmatch('[0-9a-f]{64}',hashes[key]) is None for key in keys)
            or any(type(name) is not str or not Path(name).is_absolute() or type(digest) is not str
                   or re.fullmatch('[0-9a-f]{64}',digest) is None for name,digest in files.items())):
        raise ValueError('invalid registration input')
    paths=('','research/doom','research/live_control','research/observation_gating','research/observation_tiles')
    argv=[PYTHON,str(checkout/'research/doom/session_map01_v15.py'),'--out',str(root/'runtime'),
          '--seed','990619','--timeout-seconds','75','--skill','1','--load-fixture-manifest',CANDIDATE,
          '--target-process-identity','--owned-input-service','--renewal-passive-observer','--post-load-clock-gate',
          '--door-task-arm','use','--door-task-traverse','--door-task-reverse-arm','east-return',
          '--candidate-setup-evidence',str(root/'evidence.json'),'--candidate-setup-evidence-sha256',EVIDENCE,
          '--door-expected-manifest-sha256',MANIFEST,'--door-expected-save-sha256',SAVE,
          '--door-expected-iwad-sha256',IWAD,'--door-expected-restore-tic','870']
    return {'schema':'map01-east-return-registration-v1','root':str(root),'unit':unit,'arm':'east-return',
            'checkout':str(checkout),'revision':revision,'tree':tree,'python':PYTHON,
            'pythonpath':':'.join(str(checkout/path) for path in paths),'runtime_argv':argv,
            'candidate_manifest_sha256':MANIFEST,'candidate_save_sha256':SAVE,
            'candidate_evidence_sha256':EVIDENCE,'candidate_restore_tic':870,
            'reference_png_sha256':INITIAL_REFERENCE,'visual_guard_sha256':INITIAL_GUARD,
            'east_reference_sha256':EAST_REFERENCE,**{key:hashes[key] for key in keys},
            'repeat_limit':1,'model_calls':0,'wall_deadline_seconds':48,'max_settle_polls':250,
            'unit_options':list(UNIT_OPTIONS),'files':dict(files),'endpoint_rules':deepcopy(SCOPED_RULES),
            'guard_requires_new_frame':True,
            'scope':'one X11 standard-caller endpoint trial; no model, continuous path, player floor, map completion or speed claim'}
