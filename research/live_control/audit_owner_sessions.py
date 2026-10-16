"""Source, image, input release and saved-task audit for owner self-use."""
import hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder,Frame
for name in sys.argv[1:]:
    folder=Path(name)
    for relative,digest in json.loads((folder/'sources.json').read_text()).items():
        assert hashlib.sha256((HERE.parent/relative).read_bytes()).hexdigest()==digest,relative
    rows=[json.loads(s) for s in (folder/'events.jsonl').read_text().splitlines()]
    decoder=Decoder('live-control');count=0
    for r in rows:
        if r['event']=='observation':
            frame=decoder.accept((folder/f"{r['sequence']:03d}.ait").read_bytes())
            with Image.open(folder/Path(r['image']).name) as im:
                assert frame==Frame(im.width,im.height,im.mode,im.tobytes())
            count+=1
    terms=[r for r in rows if r['event']=='terminal']
    assert terms and all(r['release']['verified'] for r in terms)
    owner=json.loads((folder/'owner-events.json').read_text())
    assert owner[-1]['reason']=='close' and owner[-1]['verified']
    score=next(r for r in rows if r['event']=='independent_evaluation')
    ready=next(r for r in rows if r['event']=='ready')
    if ready['app']=='xterm':
        actual=(folder/'submitted.txt').read_text()
        expected=ready['goal']['token']
    else:
        import openpyxl
        wb=openpyxl.load_workbook(folder/'sheet.xlsx',data_only=True)
        actual=[wb.active['A1'].value,wb.active['A2'].value];wb.close()
        expected=[ready['goal']['a'],ready['goal']['b']]
    assert actual==score['actual'] and (actual==expected)==score['success']
    latencies=[]
    for t in terms:
        start=next(r['accepted_ns'] for r in rows if r['event']=='accepted' and r['id']==t['id'])
        first=next(r for r in rows if r['event']=='observation' and r['id']==t['id'])
        latencies.append((first['image_ready_ns']-start)/1e6)
    result=dict(exact_frames=count,programs=len(terms),task_success=score['success'],actual=actual,
                owner_closed_and_release_verified=True,accept_to_first_image_ready_ms=latencies,
                scope='exploratory assistant self-use; local timing, no matched model comparison')
    (folder/'audit.json').write_text(json.dumps(result,indent=2));print(name,json.dumps(result))
