import hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder,Frame
folder=Path(sys.argv[1]);count=0
for n,h in json.loads((folder/'sources.json').read_text()).items():
    assert hashlib.sha256((HERE/n).read_bytes()).hexdigest()==h
reports=json.loads((folder/'summary.json').read_text());assert len(reports)==4
for path in folder.glob('*/report.json'):
    report=json.loads(path.read_text());assert report in reports
    rows=json.loads((path.parent/'events.json').read_text());dec=Decoder('live-control')
    assert rows[0]['event']=='observation' and not rows[0]['focus_samples_match']
    assert report['mixed_status']=='needs_decision'
    assert not any(r['event']=='input_admission' for r in rows[:next(i for i,r in enumerate(rows) if r['event']=='terminal' and r['id']=='mixed')])
    assert report['recovery_status']==('completed' if report['candidate'] else 'needs_decision')
    for r in rows:
        if r['event']=='terminal':assert r['release']['verified']
        if r['event']=='observation':
            frame=dec.accept((path.parent/f"{r['sequence']:03d}.ait").read_bytes())
            with Image.open(path.parent/Path(r['image']).name) as im:
                assert frame==Frame(im.width,im.height,im.mode,im.tobytes())
            count+=1
result=dict(episodes=4,exact_frames=count,source_hashes_verified=True,recovery_candidate_passes=2,baseline_recovery_blocks=2)
(folder/'audit.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
