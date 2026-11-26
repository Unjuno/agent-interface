"""Read-only preflight for a fresh, pinned, single-use allocation."""
import hashlib
import json
import re
import os
import subprocess
from pathlib import Path

FILES={'driver.py':'driver_sha256','launcher.py':'launcher_sha256',
       'evidence.json':'candidate_evidence_sha256','visual_guard.py':'visual_guard_sha256',
       'reference.png':'reference_png_sha256','east-reference.png':'east_reference_sha256',
       'audit.py':'auditor_sha256','preflight.py':'preflight_sha256'}


def validate_unspent(root, spec, *, expected_east_sha, expected_initial_sha, expected_guard_sha):
    root=Path(root)
    if root.is_symlink() or not root.is_dir() or root.stat().st_mode & 0o777 != 0o700 or Path(spec.get('root',''))!=root:
        raise ValueError('allocation root differs')
    if set(p.name for p in root.iterdir())!=set(FILES)|{'registration.json'}:
        raise ValueError('allocation is not unspent')
    if (spec.get('schema')!='map01-east-return-registration-v1' or spec.get('arm')!='east-return'
            or type(spec.get('repeat_limit')) is not int or spec['repeat_limit']!=1
            or type(spec.get('model_calls')) is not int or spec['model_calls']!=0
            or type(spec.get('unit')) is not str or re.fullmatch(r'map01-east-[a-z0-9]+\.service',spec['unit']) is None
            or spec.get('unit_options')!=['UMask=0077','PrivateTmp=yes','PrivateNetwork=yes',
                                         'RuntimeMaxSec=60s','TimeoutStopSec=5s','KillMode=control-group']):
        raise ValueError('registered isolation or trial bounds differ')
    python='/home/user/.cache/agent-interface-map01-20261103/bin/python'
    try:
        python_valid=(spec.get('python')==python and Path(python).resolve(strict=True)==Path('/usr/bin/python3.12')
                      and Path(python).is_file() and os.access(python,os.X_OK))
    except (OSError,RuntimeError):
        python_valid=False
    if not python_valid:
        raise ValueError('registered python is unavailable or differs')
    if spec.get('east_reference_sha256')!=expected_east_sha:
        raise ValueError('east reference does not match pinned source')
    if spec.get('reference_png_sha256')!=expected_initial_sha or spec.get('visual_guard_sha256')!=expected_guard_sha:
        raise ValueError('initial reference or visual guard differs from pinned source')
    for name,key in FILES.items():
        path=root/name
        if path.is_symlink() or not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=spec.get(key):
            raise ValueError('allocation input digest differs: '+name)
    if (root/'registration.json').is_symlink() or not (root/'registration.json').is_file():
        raise ValueError('registration is not a regular file')


def retirement_disposition(unit_absent, cgroup_absent, service_observed):
    if any(type(value) is not bool for value in (unit_absent,cgroup_absent,service_observed)):
        raise ValueError('retirement observations must be explicit booleans')
    absent=unit_absent and cgroup_absent
    return absent, absent and service_observed


def validate_runtime_inputs(root, spec, *, expected_checkout, baseline_path, baseline_sha256):
    """Check the complete fixed runtime binding before consuming the claim."""
    root=Path(root);checkout=Path(expected_checkout)
    manifest='16f2bcf78b1d7739afd1fa0c141f1bbaee9dd2c9e3ff8e356ef3df743899d8d5'
    save='4e5b990cba8a86ca8a526ecdc59798c1869ea23c8f53468369e811f41d057ddc'
    evidence='40ef78b09f62fcd1b66cc6dc08257aa7d9d3f75fa0fe0797160c3d8fd48b58dc'
    wad='a8772e088847032510d97ba2312406a6998f21cbab44d4ff10696faa9c0ecd4b'
    python='/home/user/.cache/agent-interface-map01-20261103/bin/python'
    candidate='/home/user/issue59-grandchild-bound-setup-yzkdlh9q/candidate/fixture.json'
    paths=('','research/doom','research/live_control','research/observation_gating','research/observation_tiles')
    argv=[python,str(checkout/'research/doom/session_map01_v15.py'),'--out',str(root/'runtime'),
          '--seed','990619','--timeout-seconds','75','--skill','1','--load-fixture-manifest',candidate,
          '--target-process-identity','--owned-input-service','--renewal-passive-observer','--post-load-clock-gate',
          '--door-task-arm','use','--door-task-traverse','--door-task-reverse-arm','east-return',
          '--candidate-setup-evidence',str(root/'evidence.json'),'--candidate-setup-evidence-sha256',evidence,
          '--door-expected-manifest-sha256',manifest,'--door-expected-save-sha256',save,
          '--door-expected-iwad-sha256',wad,'--door-expected-restore-tic','870']
    files=spec.get('files');revision=spec.get('revision');tree=spec.get('tree')
    if (spec.get('checkout')!=str(checkout) or spec.get('python')!=python
            or spec.get('runtime_argv')!=argv or spec.get('pythonpath')!=':'.join(str(checkout/x) for x in paths)
            or spec.get('candidate_manifest_sha256')!=manifest or spec.get('candidate_save_sha256')!=save
            or spec.get('candidate_evidence_sha256')!=evidence or spec.get('candidate_restore_tic')!=870
            or type(revision) is not str or re.fullmatch('[0-9a-f]{40}',revision) is None
            or type(tree) is not str or re.fullmatch('[0-9a-f]{40}',tree) is None or type(files) is not dict):
        raise ValueError('runtime binding differs')
    required=('session_map01_v12.py','session_map01_v15.py','map01_door_driver_protocol.py',
              'map01_door_coordinator.py','map01_door_journal.py','map01_door_task_contract.py',
              'map01_door_sector_scorer.py','map01_reverse_program.py','map01_candidate_setup_evidence_v1.py',
              'map01_post_load_gate_v1.py','map01_east_return_caller_gate.py','map01_east_return_visual_guard.py')
    if not all(str(checkout/'research/doom'/name) in files for name in required):
        raise ValueError('runtime source pins missing')
    for key,name in (('driver_sha256','map01_os_east_return_driver.py'),('launcher_sha256','map01_east_return_launcher.py'),
                     ('preflight_sha256','map01_east_return_launcher_preflight.py'),('auditor_sha256','map01_east_return_audit.py')):
        if files.get(str(checkout/'research/doom'/name))!=spec.get(key):
            raise ValueError('artifact source and copied digest differ')
    try:
        baseline_path=Path(baseline_path)
        if baseline_path.is_symlink() or not baseline_path.is_file():
            raise ValueError('baseline registration unavailable')
        baseline_bytes=baseline_path.read_bytes()
        if hashlib.sha256(baseline_bytes).hexdigest()!=baseline_sha256:
            raise ValueError('baseline registration digest differs')
        baseline=json.loads(baseline_bytes);old=baseline.get('checkout');prior=baseline.get('files')
        if (type(old) is not str or not Path(old).is_absolute() or type(prior) is not dict):
            raise ValueError('baseline registration malformed')
        for name,digest in prior.items():
            if type(name) is not str or not Path(name).is_absolute() or type(digest) is not str:
                raise ValueError('baseline pin malformed')
            if name.startswith(old+'/'):
                mapped=str(checkout/name[len(old)+1:])
                if mapped not in files:
                    raise ValueError('baseline source pin missing')
            elif files.get(name)!=digest:
                raise ValueError('baseline external pin missing or changed')
        for name,digest in files.items():
            if (type(name) is not str or not Path(name).is_absolute() or type(digest) is not str
                    or re.fullmatch('[0-9a-f]{64}',digest) is None
                    or hashlib.sha256(Path(name).read_bytes()).hexdigest()!=digest):
                raise ValueError('runtime source digest differs')
        def git(*args):
            return subprocess.check_output(['git','-C',str(checkout),*args],text=True,timeout=30).strip()
        if git('rev-parse','HEAD')!=revision or git('rev-parse','HEAD^{tree}')!=tree or git('status','--porcelain'):
            raise ValueError('runtime checkout differs or is dirty')
    except (OSError,subprocess.SubprocessError) as error:
        raise ValueError('runtime inputs unavailable') from error


def read_marker(path):
    path=Path(path)
    try:
        if path.is_symlink():
            return None,'symlink'
        payload=path.read_bytes()
    except FileNotFoundError:
        return None,'missing'
    except OSError:
        return None,'unreadable'
    try:
        row=json.loads(payload)
    except (ValueError,UnicodeError):
        return None,'invalid_json'
    if type(row) is not dict:
        return None,'invalid_shape'
    return row,'valid'
