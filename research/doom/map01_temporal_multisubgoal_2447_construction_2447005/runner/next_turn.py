from pathlib import Path
import argparse,hashlib,json,time
from PIL import ImageGrab
from Xlib import display
from common import Inputs,write

def main():
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--ctx',required=True);p.add_argument('--out',required=True);p.add_argument('--key',choices=['Right','Left'],required=True);a=p.parse_args()
    out=Path(a.out);out.mkdir(parents=True,exist_ok=False);ctx=json.loads(Path(a.ctx).read_text());events=[];inp=Inputs(a.source,ctx,events)
    lease=None
    try:
        d=display.Display(ctx['display']);root=d.screen().root;focus=d.get_input_focus().focus.id;win=d.create_resource_object('window',ctx['surface']);geo=win.get_geometry();pos=root.translate_coords(win,0,0)
        current_geometry=[pos.x,pos.y,geo.width,geo.height]
        if focus!=ctx['focus'] or current_geometry!=ctx['geometry']:raise RuntimeError('FRESH_OBSERVATION_BINDING_MISMATCH')
        observation_ns=time.perf_counter_ns();im=ImageGrab.grab(xdisplay=ctx['display']).convert('RGB').crop((pos.x,pos.y,pos.x+geo.width,pos.y+geo.height));pixel_sha=hashlib.sha256(im.tobytes()).hexdigest();im.save(out/'handoff-observation.png');d.close()
        lease=inp.lease(.19)
        down=inp.owner.call('down',lease,a.key)
        down_done_ns=time.perf_counter_ns();time.sleep(.19)
        up_started_ns=time.perf_counter_ns();inp.owner.call('up',lease,a.key)
        release=inp.release(lease);release_done_ns=time.perf_counter_ns()
        purpose='subgoal_turn_'+a.key.lower();events.append(dict(kind='input',purpose=purpose,keys=[a.key],requested_seconds=.19,down=down,down_done_ns=down_done_ns,up_started_ns=up_started_ns,release=release,release_done_ns=release_done_ns))
        write(out/'result.json',dict(next_subgoal_issued=True,key=a.key,requested_seconds=.19,observation_ns=observation_ns,observation_sha256=pixel_sha,observation_binding={'focus':focus,'surface':ctx['surface'],'geometry':current_geometry},down_done_ns=down_done_ns,up_started_ns=up_started_ns,release_done_ns=release_done_ns,release=release))
        write(out/'events.json',events);write(out/'owner-records.json',inp.owner.records)
        time.sleep(.02)
    finally: inp.close()
if __name__=='__main__':main()

