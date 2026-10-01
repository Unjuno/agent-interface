"""Replay exact images and independent delivery score for actual visual self-use."""
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
from PIL import Image
from mindustry_bend_build_score_v1 import score

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'observation_tiles'))
from tile_transport import Decoder

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())

def main():
    root=HERE/'results/mindustry-bend-self-use-02';manifest=read(root/'manifest.json')
    for path,digest in manifest['sources'].items():assert sha(HERE.parent/path)==digest,path
    initial,delivery,after=[read(root/name) for name in ('before.json','delivery-before.json','after.json')]
    assert initial['paused'] is True and initial['player_dead'] is False and initial['unit']['plans']==0
    assert delivery['paused'] is True and delivery['unit']['plans']==0
    assert all(math.isfinite(s['tick']) and type(s['copper']) is int for s in (initial,delivery,after))
    plan=read(HERE/'mindustry_bend_plan_v1.json');actual=score(initial,delivery,after,plan)
    assert actual==read(root/'evaluation.json') and actual['contract_satisfied'] is True
    events=[json.loads(line) for line in (root/'events.jsonl').read_text().splitlines()]
    observations=[e for e in events if e['event']=='observation'];decoder=Decoder('live-control')
    for n,e in enumerate(observations,1):
        assert e['sequence']==n
        frame=decoder.accept((root/f'{n:03d}.ait').read_bytes())
        with Image.open(root/Path(e['image']).name) as im:
            assert (im.width,im.height,im.mode,im.tobytes())==(frame.width,frame.height,frame.mode,frame.pixels)
    admissions=[e for e in events if e['event']=='accepted'];terminals=[e for e in events if e['event']=='terminal']
    assert len(admissions)==len(terminals)==4 and not any(e['event']=='rejected' for e in events)
    assert [e['id'] for e in admissions]==[e['id'] for e in terminals]
    assert all(e['status']=='completed' and e['release']['verified'] is True for e in terminals)
    finish=next(e for e in events if e['event']=='command' and e['command']['op']=='finish')
    evaluation=next(e for e in events if e['event']=='independent_evaluation')
    assert not any(e['event'] in ('accepted','input_admission','pointer_admission') for e in events[events.index(finish)+1:])
    assert read(root/'cleanup.json')=={'all_owned_processes_exited':True,'save_unchanged':True}
    decision=read(root/'gui-decision.json')
    assert decision['final_image_sha256']==sha(root/'018.png')
    commitment=next(e for e in events if e['event']=='command' and e['command'].get('gui_decision_sha256')==sha(root/'gui-decision.json'))
    assert events.index(commitment)<events.index(finish)
    aborted=HERE/'results/mindustry-bend-self-use-01'
    prior=[json.loads(line) for line in (aborted/'events.jsonl').read_text().splitlines()]
    assert not any(e['event']=='accepted' for e in prior)
    assert read(aborted/'cleanup.json')==read(root/'cleanup.json')
    controls={}
    for name in ('zero_delivery','pending_build','unpaused_baseline','short_window','changed_layout','negative_initial_net','wrong_direction','nan_tick'):
        i,d,a=copy.deepcopy(initial),copy.deepcopy(delivery),copy.deepcopy(after)
        if name=='zero_delivery':a['copper']=d['copper'];expected=False
        elif name=='pending_build':d['unit']['plans']=1;expected=None
        elif name=='unpaused_baseline':d['paused']=False;expected=None
        elif name=='short_window':d['tick']=a['tick']-1;expected=None
        elif name=='changed_layout':d['tiles'][0]['block']='conveyor';expected=False
        elif name=='wrong_direction':
            for snapshot in (d,a):
                next(t for t in snapshot['tiles'] if (t['x'],t['y'])==(139,51))['rotation']=0
            expected=False
        elif name=='nan_tick':d['tick']=float('nan');expected=None
        else:i['copper']=a['copper']+100;expected=True
        result=score(i,d,a,plan);assert result['contract_satisfied'] is expected,(name,result)
        controls[name]=result
    report={'scope':'one known visual construction episode; no held-out performance or global verifier claim',
        'exact_frames':len(observations),'accepted_programs':len(admissions),'rejected_programs':0,
        'visual_recoveries':[],
        'visual_review_sequences':[1,4,11,13,18],
        'initial_copper':initial['copper'],'post_control_copper':delivery['copper'],'final_copper':after['copper'],
        'delivery_copper':actual['copper_delta'],'delivery_ticks':actual['delivery_ticks'],
        'initial_capture_to_last_terminal_ms':(terminals[-1]['terminal_ns']-observations[0]['capture_ns'])/1e6,
        'initial_capture_to_evaluation_ms':(evaluation['emitted_ns']-observations[0]['capture_ns'])/1e6,
        'finish_to_evaluation_ms':(evaluation['emitted_ns']-finish['emitted_ns'])/1e6,
        'between_program_gaps_ms':[(b['accepted_ns']-a['terminal_ns'])/1e6 for a,b in zip(terminals,admissions[1:])],
        'score_controls':controls,'model_tokens':None,'model_receipt_ns':None,
        'audit_sha256':sha(Path(__file__))}
    (root/'audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k!='score_controls'},indent=2))

if __name__=='__main__':main()
