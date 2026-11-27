"""Audit one sealed synthetic Xvfb HUD/owner trial; no game or input is run."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent
RAW = ROOT / 'raw'
SOURCE = ROOT / 'source'
SEAL = 'bcf99f8d7be0126358d0e2a2e0b248d8296ef53617c9d6d799178709c3ecfd56'


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wad', required=True, type=Path)
    args = parser.parse_args()
    seal_bytes = (RAW / 'seal.json').read_bytes()
    require(sha(seal_bytes) == SEAL, 'seal differs')
    seal = json.loads(seal_bytes)
    for name, row in seal['files'].items():
        path = RAW / name
        require(path.is_file() and not path.is_symlink(), 'missing sealed file')
        content = path.read_bytes()
        require(len(content) == row['bytes'] and sha(content) == row['sha256'], 'sealed file differs')
    plan = json.loads((RAW / 'registration.json').read_bytes())
    manifest = (SOURCE / 'SOURCE_MANIFEST.json').read_bytes()
    require(sha(manifest) == plan['source_manifest_sha256'], 'source manifest differs')
    pinned = {row['path']: row for row in json.loads(manifest)['files']}
    for name, path in [('doom_hud_signal_v1.py','research/doom/doom_hud_signal_v1.py'),
                       ('doom_hud_signal_v2.py','research/doom/doom_hud_signal_v2.py'),
                       ('doom_hud_signal_v3.py','research/doom/doom_hud_signal_v3.py'),
                       ('observable_signal_guard_v2.py','research/live_control/observable_signal_guard_v2.py')]:
        content = (SOURCE / name).read_bytes()
        require(len(content) == pinned[path]['bytes'] and sha(content) == pinned[path]['sha256'], 'source differs')
    require(sha((SOURCE / 'baseline_hud_signal_v1.py').read_bytes()) == plan['baseline_reader_sha256'], 'baseline differs')
    with args.wad.open('rb') as stream:
        require(hashlib.file_digest(stream, 'sha256').hexdigest() == plan['wad_sha256'], 'WAD differs')
    sys.path.insert(0, str(SOURCE))
    from doom_hud_signal_v3 import DoomStatusNumberReader
    from observable_signal_guard_v2 import ObservableSignalGuard
    spec = importlib.util.spec_from_file_location('baseline_hud_audit', SOURCE / 'baseline_hud_signal_v1.py')
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    with Image.open(RAW / 'clean.png') as image:
        clean = image.convert('RGB')
    with Image.open(RAW / 'occluded.png') as image:
        occluded = image.convert('RGB')
    delta = np.any(np.asarray(clean) != np.asarray(occluded), axis=2)
    ys, xs = np.where(delta)
    require(int(delta.sum()) == 114 and (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())) == (435,591,437,628), 'occlusion differs')
    events = {row['event']: row for row in json.loads((RAW / 'events.json').read_bytes())}
    source = events['source_signal']['signal']
    current = events['candidate_signal']['signal']
    binding = source['binding']
    obs1 = {'sequence': source['sequence'], 'capture_ns': source['capture_ns'], 'pointer_binding': binding, 'image': str(RAW / 'clean.png')}
    obs2 = {'sequence': current['sequence'], 'capture_ns': current['capture_ns'], 'pointer_binding': binding, 'image': str(RAW / 'occluded.png')}
    reader = DoomStatusNumberReader(args.wad, signal_id='health')
    c1, c2 = reader.read_frame(obs1, clean), reader.read_frame(obs2, occluded)
    old = baseline.DoomStatusNumberReader(args.wad).read(obs2)
    require(c1['status'] == 'observed' and c1['value'] == 100 and c2['status'] == 'unknown' and c2['reason'] == 'unverified_leading_blank' and old['status'] == 'observed' and old['value'] == 0, 'reader results differ')
    guard = ObservableSignalGuard({'op':'observable_signal_guard','guard_id':'owned-hud','source_sequence':1,'signal_id':'health','source_value':100,'hard_minimum':80,'max_source_age_ms':10000,'on_soft_change':'preserve_existing_policy','on_hard_change':'needs_decision','on_unknown':'needs_decision'}, c1, binding)
    outcome = guard.evaluate(c2)
    require(outcome == events['guard_outcome']['outcome'] and outcome['status'] == 'UNKNOWN' and outcome['requires_new_decision'] is True and outcome['grants_input_authority'] is False, 'guard differs')
    ack = events['key_admission']['ack']
    release = events['owner_interruption']['receipt']['record']
    attempt = release['key_release_attempts'][str(ack['keycode'])]['attempts'][0]
    require(release['verified'] is True and release['reason'] == 'cancelled' and all(release[k] == [] for k in ('keys_down','keys_unknown','buttons_down','key_state_errors')) and attempt['server_key_down_before'] is True and attempt['server_key_down_after'] is False and ack['input_ack_ns'] <= attempt['keyrelease_started_ns'] <= attempt['keymap_sampled_ns'] <= release['verified_ns'], 'release differs')
    outcome = json.loads((RAW / 'launcher-outcome.json').read_bytes())
    require(outcome['exit_code'] == 0 and outcome['timeout'] is False and 'LoadState=not-found' in outcome['service_state'] and seal['service_retired'] is True, 'service retirement differs')
    print(json.dumps({'status':'PASS','sealed_files':len(seal['files']),'changed_pixels':int(delta.sum()),'baseline_occluded':0,'candidate':'UNKNOWN','guard':'UNKNOWN','release':'X11 verified','scope':'synthetic owned Xvfb display; no live game or model'},indent=2))


if __name__ == '__main__':
    main()
