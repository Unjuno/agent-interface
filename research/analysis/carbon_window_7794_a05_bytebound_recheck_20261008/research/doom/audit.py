import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder,Frame


def audit(folder):
    for relative,expected in json.loads((folder/'sources.json').read_text()).items():
        assert hashlib.sha256((HERE.parent/relative).read_bytes()).hexdigest()==expected,relative
    rows=[json.loads(s) for s in (folder/'events.jsonl').read_text().splitlines()]
    decoder=Decoder('live-control');count=0
    for row in rows:
        if row['event']!='observation':continue
        frame=decoder.accept((folder/f'{row["sequence"]:03d}.ait').read_bytes())
        with Image.open(folder/Path(row['image']).name) as im:
            assert frame==Frame(im.width,im.height,im.mode,im.tobytes())
        count+=1
    terminals=[r for r in rows if r['event']=='terminal']
    assert terminals and all(r['release']['verified'] for r in terminals)
    clock=next(r for r in rows if r['event']=='clock_probe')
    score=next(r for r in rows if r['event']=='post_control_score')
    result=dict(exact_frames=count,programs=len(terminals),all_release_verified=True,
                clock_probe=clock,post_control_score=score,
                scope='assistant-operated integration development, no general game-skill benchmark')
    if clock.get('refresh_calls_outside_wait')==2:
        rate=(clock['after_tic']-clock['before_tic'])/clock['wall_seconds']
        assert 33<=rate<=37
        result['clock_probe_tics_per_wall_second']=rate
    else:result['clock_probe_valid']=False
    return result


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('folder',type=Path);a=ap.parse_args()
    result=audit(a.folder);(a.folder/'audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
