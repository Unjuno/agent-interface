import argparse,hashlib,json,sys
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder,Frame
from run import locate


def audit(folder):
    for relative,expected in json.loads((folder/'sources.json').read_text()).items():
        assert hashlib.sha256((HERE.parent/relative).read_bytes()).hexdigest()==expected,relative
    rows=[json.loads(line) for line in (folder/'events.jsonl').read_text().splitlines()]
    decoder=Decoder('live-control');frames={};count=0
    for r in rows:
        if r['event']=='observation':
            frame=decoder.accept((folder/f'{r["sequence"]:03d}.ait').read_bytes())
            with Image.open(folder/Path(r['image']).name) as im:
                assert frame==Frame(im.width,im.height,im.mode,im.tobytes())
                frames[r['sequence']]=locate(im)
            count+=1
        elif r['event']=='motor_feedback':
            assert frames[r['sequence']]==(r['target_x'],r['player_x'])
    accepted=next(r for r in rows if r['event']=='accepted')
    cancel=next(r for r in rows if r['event']=='cancel_requested')
    terminal=next(r for r in rows if r['event']=='terminal')
    assert cancel['matched'] and terminal['status']=='cancelled' and terminal['release']['verified']
    assert terminal['steps_completed']==1
    assert not any(r['event']=='step_started' and r['step']==2 for r in rows)
    assert not any(r['event']=='motor_feedback' and r['input_ack_ns']>terminal['terminal_ns'] for r in rows)
    assert any(r['event']=='independent_record' and r.get('frames',0)>0 for r in rows)
    # Replay both presentation policies over this same event trace, excluding PTY
    # echo/wrapping. These are UTF-8 JSON byte counts, not tokenizer measurements.
    def size(r):return len((json.dumps(r)+'\n').encode())
    full=sum(size(r) for r in rows);compact=0;seen=set();latest=None;shown=0
    for r in rows:
        k=r['event']
        if k=='observation':
            latest=r;key=(r['id'],r['step'])
            if key in seen:continue
            seen.add(key)
        elif k in ('motor_feedback','command'):continue
        if k=='terminal':r={**r,'latest_sequence':latest['sequence'],'latest_image':latest['image']}
        compact+=size(r);shown+=1
    polls=[r for r in rows if r['event']=='latest_observation']
    first_image=next(r for r in rows if r['event']=='observation' and r['id']==accepted['id'] and r['step']==1)
    first_motor=next(r for r in rows if r['event']=='motor_feedback')
    return dict(exact_frames=count,motor_decisions=sum(r['event']=='motor_feedback' for r in rows),
        cancellation_matched=True,release_verified=True,
        accepted_to_cancel_seconds=(cancel['requested_ns']-accepted['accepted_ns'])/1e9,
        cancel_to_release_ms=(terminal['release']['verified_ns']-cancel['requested_ns'])/1e6,
        accept_to_first_tracking_image_ready_ms=(first_image['image_ready_ns']-accepted['accepted_ns'])/1e6,
        accept_to_first_motor_ack_ms=(first_motor['input_ack_ns']-accepted['accepted_ns'])/1e6,
        poll_observation_age_ms=[r['observation_age_ms'] for r in polls],
        same_trace_full_json_bytes=full,same_trace_compact_json_bytes=compact,
        compact_records=shown,full_records=len(rows),
        scope='assistant-operated local integration; presentation replay bytes are not model tokens or efficacy evidence')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('folder',type=Path);a=ap.parse_args()
    report=audit(a.folder);(a.folder/'audit.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))
