"""Audit the recorded assistant boundary trial; never controls the application."""
import json
import sys
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder,Frame


def audit(folder):
    events=[json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines()]
    boundary=next(e for e in events if e['event']=='terminal' and e['id']=='bounded')
    assert boundary['status']=='needs_decision' and boundary['release']['verified']
    assert not any(e['event']=='step_started' and e['id']=='bounded' and e['step']==2 for e in events)
    assert not any(e['event']=='accepted' and e['id']=='stale' for e in events)
    assert any(e['event']=='rejected' and 'sequence' in e['reason'] for e in events)
    fresh=next(e for e in events if e['event']=='command' and e['command'].get('id')=='fresh')
    assert events[-1]['event']=='independent_evaluation' and events[-1]['success']
    decoder=Decoder('live-control');count=0
    for e in events:
        if e['event']!='observation':continue
        frame=decoder.accept((folder/f'{e["sequence"]:03d}.ait').read_bytes())
        # Stored absolute paths are historical; use the immutable basename locally.
        with Image.open(folder/Path(e['image']).name) as im:
            assert frame==Frame(im.width,im.height,im.mode,im.tobytes())
        count+=1
    return dict(boundary_stopped_tail=True,release_verified=True,stale_request_rejected=True,
                fresh_task_success=True,frames_verified=count,
                boundary_to_fresh_request_seconds=(fresh['received_ns']-boundary['terminal_ns'])/1e9,
                scope='one assistant-operated development trial, not a controlled efficacy comparison')


if __name__=='__main__':
    folder=Path(sys.argv[1]);result=audit(folder)
    (folder/'decision-audit.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
