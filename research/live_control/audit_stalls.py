"""Audit recorded stall probes without rerunning their GUI actions."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder, Frame


def audit(folder):
    for name, digest in json.loads((folder/'sources.json').read_text()).items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest() == digest, name
    reports = json.loads((folder/'summary.json').read_text())
    episodes = sorted(folder.glob('*/report.json'))
    assert len(reports) == len(episodes) and reports
    frames = 0
    owner_delays = []
    for path in episodes:
        report = json.loads(path.read_text())
        assert report in reports
        run = path.parent
        events = json.loads((run/'events.json').read_text())
        terminal, = [e for e in events if e['event']=='terminal']
        assert terminal['status']=='expired' and terminal['release']['verified']
        assert not any(e['event']=='step_started' and e['step']>0 for e in events)
        assert all(e['admitted_ns']<e['valid_until_ns'] for e in events if e['event']=='input_admission')
        samples = json.loads((run/'key-samples.json').read_text())
        assert all(a['ns']<=b['ns'] for a,b in zip(samples,samples[1:]))
        down = [s for s in samples if s['down']]
        up = next(s for s in samples if not s['down'] and s['ns']>down[-1]['ns'])
        assert report['first_observed_up_after_deadline_ms']==(up['ns']-report['deadline_ns'])/1e6
        assert report['last_observed_down_after_deadline_ms']==(down[-1]['ns']-report['deadline_ns'])/1e6
        decoder = Decoder('live-control')
        for e in events:
            if e['event']!='observation':
                continue
            frame = decoder.accept((run/f'{e["sequence"]:03d}.ait').read_bytes())
            with Image.open(run/Path(e['image']).name) as im:
                assert frame==Frame(im.width, im.height, im.mode, im.tobytes())
            frames += 1
        if report.get('isolated'):
            owner = json.loads((run/'owner-events.json').read_text())
            expiry, = [r for r in owner if r['reason']=='expired']
            assert expiry['verified']
            owner_delays.append((expiry['verified_ns']-report['deadline_ns'])/1e6)
    return dict(episodes=len(episodes), exact_frames=frames, source_hashes_verified=True,
                all_tails_stopped=True, all_terminal_releases_verified=True,
                owner_expiry_verification_after_deadline_ms=owner_delays,
                scope='local injected-stall control probes; no saved-task score or model comparison')


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('folder',type=Path)
    args=ap.parse_args()
    result=audit(args.folder)
    (args.folder/'audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
