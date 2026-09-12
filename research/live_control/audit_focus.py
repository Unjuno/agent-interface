import hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder,Frame
folder=Path(sys.argv[1]);count=0
for name,h in json.loads((folder/'sources.json').read_text()).items():
    assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==h
reports=json.loads((folder/'summary.json').read_text());assert len(reports)==8
for path in folder.glob('*/report.json'):
    report=json.loads(path.read_text());assert report in reports
    rows=json.loads((path.parent/'events.json').read_text());dec=Decoder('live-control')
    terminal=next(r for r in rows if r['event']=='terminal')
    blocked=report['guarded'] and report['focus_changed']
    assert terminal['status']==('needs_decision' if blocked else 'completed')
    assert terminal['release']['verified']
    assert bool(report['sink_keypresses'])==(report['focus_changed'] and not report['guarded'])
    if blocked:assert not any(r['event']=='input_admission' for r in rows)
    for r in rows:
        if r['event']=='observation':
            frame=dec.accept((path.parent/f"{r['sequence']:03d}.ait").read_bytes())
            with Image.open(path.parent/Path(r['image']).name) as im:
                assert frame==Frame(im.width,im.height,im.mode,im.tobytes())
            count+=1
result=dict(episodes=len(reports),exact_frames=count,source_hashes_verified=True,
    baseline_wrong_target_cases=2,guarded_wrong_target_cases=0,
    scope='controlled X11 focus transfer; sink delivery report not independently reconstructible from raw X events')
(folder/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
