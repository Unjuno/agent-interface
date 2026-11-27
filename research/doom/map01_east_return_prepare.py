"""Prepare, but do not launch, one new pinned east-return allocation."""
import hashlib
import json
import os
import secrets
import subprocess
import sys
from pathlib import Path

CHECKOUT=Path('/home/user/issue59-door-effect')
WORKSPACE=Path('/mnt/c/Users/user/Documents/Codex/2026-10-03/new-chat-2')
BASELINE=Path('/home/user/issue59-grandchild-bound-setup-yzkdlh9q/registration.json')
CANDIDATE=BASELINE.parent/'candidate/fixture.json'
CALIBRATION=Path('/home/user/issue59-os-reverse-turn-calibrate-muz9f0rw')
PRIOR_USE=Path('/home/user/issue59-os-reverse-pair-use-f1r597mn')
BASELINE_SHA='4dbe44082da117dde60a7713157065bcc5d490bf720a9a988b1e0e7707b4ee6d'
CALIBRATION_SEAL='4ff6a13b38329f9f4554adea30a33b89607998b1e7d06bb4a29e7aa6f91ec526'
PRIOR_USE_SEAL='169e6621e76a3ce3049d59186191e79be5033bba37c4fb22c0444583449080d6'


def sha(path):
    with Path(path).open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def write_exclusive(path, data):
    descriptor=os.open(path,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(descriptor,'wb') as stream:
        stream.write(data);stream.flush();os.fsync(stream.fileno())


def prepare(*, timed_hold=False, arm='east-return'):
    sys.path[:0]=[str(CHECKOUT/'research/doom'),str(CHECKOUT/'research/live_control'),str(CHECKOUT)]
    from map01_candidate_setup_evidence_v1 import read_sealed_directory
    from map01_east_return_registration import build_spec,MANIFEST,SAVE,EVIDENCE,INITIAL_REFERENCE,INITIAL_GUARD,EAST_REFERENCE
    def git(*args):return subprocess.check_output(['git','-C',str(CHECKOUT),*args],text=True,timeout=30).strip()
    if git('status','--porcelain'):raise ValueError('checkout must be committed and clean before registration')
    revision=git('rev-parse','HEAD');tree=git('rev-parse','HEAD^{tree}')
    if BASELINE.is_symlink():raise ValueError('baseline registration differs')
    baseline_bytes=BASELINE.read_bytes()
    if hashlib.sha256(baseline_bytes).hexdigest()!=BASELINE_SHA:raise ValueError('baseline registration differs')
    baseline=json.loads(baseline_bytes);old=baseline['checkout']
    if sha(CANDIDATE)!=MANIFEST or sha(CANDIDATE.with_name('fixture.png'))!=SAVE:
        raise ValueError('candidate bytes differ')
    evidence=WORKSPACE/'map01_yzkdlh9q_corrected_setup_evidence.json'
    if sha(evidence)!=EVIDENCE:raise ValueError('candidate evidence differs')
    # These are old sealed observations used only as image references; no old runtime is restarted.
    read_sealed_directory(CALIBRATION,CALIBRATION_SEAL,expected_pass=True)
    read_sealed_directory(PRIOR_USE,PRIOR_USE_SEAL,expected_pass=True)
    initial_reference=CALIBRATION/'runtime/094.png';initial_guard=PRIOR_USE/'visual_guard.py'
    east_reference=PRIOR_USE/'runtime/122.png'
    for path,digest in ((initial_reference,INITIAL_REFERENCE),(initial_guard,INITIAL_GUARD),(east_reference,EAST_REFERENCE)):
        if path.is_symlink() or sha(path)!=digest:raise ValueError('reference bytes differ')
    pins={}
    for name,digest in baseline['files'].items():
        path=CHECKOUT/name[len(old)+1:] if name.startswith(old+'/') else Path(name)
        if not path.is_file() or (not name.startswith(old+'/') and sha(path)!=digest):
            raise ValueError('baseline source or external pin differs')
        pins[str(path)]=sha(path)
    for name in ('map01_door_coordinator.py','map01_door_journal.py','map01_door_task_contract.py',
                 'map01_door_sector_scorer.py','map01_door_driver_protocol.py','map01_reverse_program.py',
                 'map01_east_return_caller_gate.py','map01_east_return_visual_guard.py',
                 'map01_east_return_registration.py','map01_east_return_classification.py',
                 'map01_east_return_launcher.py','map01_east_return_launcher_preflight.py',
                 'map01_east_return_audit.py','map01_os_east_return_driver.py'):
        path=CHECKOUT/'research/doom'/name
        if not path.is_file():raise ValueError('required source is absent')
        pins[str(path)]=sha(path)
    if timed_hold:
        for relative in ('research/doom/session_v4.py','research/doom/session_owned_owner_backend.py',
                         'research/doom/doom_owner_thread_release_batch_backend_v1.py',
                         'research/doom/doom_process_identity_backend_v1.py',
                         'research/live_control/session_v4.py','research/live_control/input_owner_v12.py','research/live_control/input_owner_rpc_v2.py',
                         'research/live_control/input_owner_process_v3.py','research/live_control/input_owner_service_adapter.py'):
            path=CHECKOUT/relative
            if not path.is_file():raise ValueError('timed owner source is absent')
            pins[str(path)]=sha(path)
    artifacts={'driver.py':CHECKOUT/'research/doom/map01_os_east_return_driver.py',
               'launcher.py':CHECKOUT/'research/doom/map01_east_return_launcher.py',
               'preflight.py':CHECKOUT/'research/doom/map01_east_return_launcher_preflight.py',
               'audit.py':CHECKOUT/'research/doom/map01_east_return_audit.py',
               'evidence.json':evidence,'visual_guard.py':initial_guard,'reference.png':initial_reference,
               'east-reference.png':east_reference}
    artifact_bytes={name:path.read_bytes() for name,path in artifacts.items()}
    if (hashlib.sha256(artifact_bytes['evidence.json']).hexdigest()!=EVIDENCE
            or hashlib.sha256(artifact_bytes['visual_guard.py']).hexdigest()!=INITIAL_GUARD
            or hashlib.sha256(artifact_bytes['reference.png']).hexdigest()!=INITIAL_REFERENCE
            or hashlib.sha256(artifact_bytes['east-reference.png']).hexdigest()!=EAST_REFERENCE):
        raise ValueError('artifact changed during preparation')
    hashes={key:hashlib.sha256(artifact_bytes[name]).hexdigest() for name,key in
            (('driver.py','driver_sha256'),('launcher.py','launcher_sha256'),('preflight.py','preflight_sha256'),('audit.py','auditor_sha256'))}
    for key,name in (('driver_sha256','map01_os_east_return_driver.py'),('launcher_sha256','map01_east_return_launcher.py'),
                     ('preflight_sha256','map01_east_return_launcher_preflight.py'),('auditor_sha256','map01_east_return_audit.py')):
        if pins.get(str(CHECKOUT/'research/doom'/name))!=hashes[key]:
            raise ValueError('artifact source changed during preparation')
    token=secrets.token_hex(8);root=Path('/home/user')/('issue59-os-east-return-'+token);unit='map01-east-'+token+'.service'
    spec=build_spec(root,unit,CHECKOUT,revision,tree,pins,hashes,timed_hold=timed_hold,arm=arm)
    # The first filesystem mutation creates a new private root, after all source checks.
    os.mkdir(root,0o700)
    for name,data in artifact_bytes.items():write_exclusive(root/name,data)
    payload=(json.dumps(spec,sort_keys=True,indent=2,allow_nan=False)+'\n').encode()
    write_exclusive(root/'registration.json',payload)
    return {'root':str(root),'unit':unit,'registration_sha256':hashlib.sha256(payload).hexdigest(),
            'revision':revision,'pinned_files':len(pins),'launched':False}


if __name__=='__main__':
    import argparse
    parser=argparse.ArgumentParser()
    parser.add_argument('--owner-timed-hold',action='store_true')
    parser.add_argument('--arm',choices=('east-return','east-return-turn75'),default='east-return')
    args=parser.parse_args()
    os.umask(0o077)
    print(json.dumps(prepare(timed_hold=args.owner_timed_hold,arm=args.arm),sort_keys=True))
