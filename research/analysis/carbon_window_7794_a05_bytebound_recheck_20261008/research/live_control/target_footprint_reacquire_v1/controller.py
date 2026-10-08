"""Pixel-only reference target reacquisition, ordinary owner admission, Delete/Save."""
from pathlib import Path
import argparse, hashlib, json, time
import cv2, numpy as np
from PIL import Image
from common import Inputs,screenshot,write
from reference_controller_v3 import Matcher
from resolver import resolve,center_gate,MAX_AGE_NS
cv2.setNumThreads(1)


def run(source,config,out):
    c=json.loads(Path(config).read_text());out=Path(out);out.mkdir(exist_ok=False)
    ref=np.asarray(Image.open(c['reference']).convert('RGB'));tpl=np.asarray(Image.open(c['template']).convert('RGB'))
    events=[];inp=Inputs(source,c['context'],events);t0=time.perf_counter_ns();decision='UNSET';index=0
    def capture(kind):
        nonlocal index
        start=time.perf_counter_ns();im=screenshot(c['context']['display'],c['box']);end=time.perf_counter_ns()
        arr=np.asarray(im);filename=f'{index:03d}.png';index+=1;im.save(out/filename)
        events.append(dict(kind=kind,image=filename,capture_started_ns=start,capture_ns=end,rgb_sha256=hashlib.sha256(arr.tobytes()).hexdigest()))
        return arr,end
    try:
        image,cap=capture('scene_observation');start=time.perf_counter_ns();match=Matcher(ref).locate(image)
        events.append(dict(kind='scene_match',compute_ns=time.perf_counter_ns()-start,result=match))
        if not match['valid']:decision='YIELD_SCENE';return
        mat=np.asarray(match['homography']);point=cv2.perspectiveTransform(np.float32(c['point']).reshape(1,1,2),mat)[0,0].tolist()
        accepted=None
        for attempt in range(2):
            image,cap=capture('target_observation');start=time.perf_counter_ns()
            result=resolve(image,tpl,point) if c['mode']=='footprint' else center_gate(ref,image,c['point'],point)
            age=time.perf_counter_ns()-cap
            stable=(accepted is None or max(abs(a-b) for a,b in zip(result.get('point',[]),accepted['point']))<=2)
            ok=bool(result['eligible'] and age<=MAX_AGE_NS and stable)
            events.append(dict(kind='target_gate',attempt=attempt,result=result,eligible=ok,age_ns=age,compute_ns=time.perf_counter_ns()-start,stable=stable))
            if not ok:decision='YIELD_'+result['status'] if not result['eligible'] else 'YIELD_FRESHNESS';return
            accepted=result
            if attempt==0:time.sleep(.08)
        decision='ADMITTED';x,y=accepted['point']
        inp.click(c['box'][0]+x,c['box'][1]+y)
        inp.press('Delete',purpose='delete_target');inp.press(['Control_L','s'],purpose='save_document')
        time.sleep(.25);capture('post_action_observation');decision='PROGRAM_COMPLETE'
    except Exception as exc:
        decision='ERROR';events.append(dict(kind='error',detail=repr(exc)))
    finally:
        inp.close();write(out/'trace.json',dict(decision=decision,events=events,owner_records=inp.owner.records,elapsed_ns=time.perf_counter_ns()-t0,model_calls=0))
        print(json.dumps(dict(decision=decision,observations=index)),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--source',required=True);p.add_argument('--config',required=True);p.add_argument('--out',required=True);a=p.parse_args();run(a.source,a.config,a.out)
