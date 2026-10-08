#!/usr/bin/env python3
"""Posthoc screenshot-to-video alignment for retained Astra MAP01 evidence."""
import hashlib, json, math, subprocess, tempfile
from pathlib import Path
from PIL import Image, ImageChops, ImageStat

ROOT = Path(__file__).resolve().parents[3]
SRC = ROOT / "research/doom/results/map01-astra-attempt-v1"
OUT = Path(__file__).with_name("ALIGNMENT_RESULT.json")
ANCHORS = [39, 76, 117, 148, 211, 252, 293, 336, 378, 417, 459, 504]

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(1<<20),b''): h.update(b)
    return h.hexdigest()

def main():
    events=[json.loads(s) for s in (SRC/'events.jsonl').read_text().splitlines()]
    decisions=json.loads((SRC/'report.json').read_text())['decisions']
    observations={e['sequence']:e for e in events if e.get('event')=='observation'}
    video=SRC/'map01-astra-live-01-2x.mp4'
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(['ffmpeg','-v','error','-i',str(video),'-vf','crop=640:480:0:80','-vsync','0',f'{td}/f_%04d.png'],check=True)
        frames=sorted(Path(td).glob('f_*.png'))
        decoded=[Image.open(path).convert('RGB') for path in frames]
        reduced=[im.resize((160,120),Image.Resampling.LANCZOS) for im in decoded]
        rows=[]
        hud={}
        for i,seq in enumerate(ANCHORS,1):
            event=observations[seq]
            ref_full=Image.open(SRC/f'frames/{i:02d}.png').convert('RGB').crop((321,180,961,660))
            ref=ref_full.resize((160,120),Image.Resampling.LANCZOS)
            ds=[]
            for im,path in zip(reduced,frames):
                ds.append((ImageStat.Stat(ImageChops.difference(ref,im)).mean[0],int(path.stem[2:])-1))
            best=sorted(ds)[:5]
            rows.append({'sequence':seq,'capture_ns':event['capture_ns'],'best_frames':[{'frame':f,'mae':round(d,6)} for d,f in best]})
            if i in (11,12):
                hud[i]=ref_full.crop((165,405,235,460))
        health=[]
        for path,imfull in zip(frames,decoded):
            f=int(path.stem[2:])-1
            if 647 <= f <= 708:
                im=imfull.crop((165,405,235,460))
                health.append({'frame':f,'mae_to_4pct':ImageStat.Stat(ImageChops.difference(hud[11],im)).mean[0],'mae_to_0pct':ImageStat.Stat(ImageChops.difference(hud[12],im)).mean[0]})
    # Least squares fit frame = slope * seconds-from-first-capture + intercept.
    xs=[(r['capture_ns']-rows[0]['capture_ns'])/1e9 for r in rows]
    ys=[r['best_frames'][0]['frame'] for r in rows]
    xm=sum(xs)/len(xs); ym=sum(ys)/len(ys)
    slope=sum((x-xm)*(y-ym) for x,y in zip(xs,ys))/sum((x-xm)**2 for x in xs)
    intercept=ym-slope*xm
    residual=[y-(slope*x+intercept) for x,y in zip(xs,ys)]
    loo=[]
    for j in range(len(xs)):
        xx=[x for k,x in enumerate(xs) if k!=j]; yy=[y for k,y in enumerate(ys) if k!=j]
        a=sum((x-sum(xx)/len(xx))*(y-sum(yy)/len(yy)) for x,y in zip(xx,yy))/sum((x-sum(xx)/len(xx))**2 for x in xx)
        b=sum(yy)/len(yy)-a*sum(xx)/len(xx)
        loo.append(ys[j]-(a*xs[j]+b))
    accept=next(e for e in events if e.get('event')=='accepted' and e.get('id')=='plan-11-primary-0-2')['accepted_ns']
    model_start_ns=decisions[11]['controller_model_started_ns']
    model_end_ns=decisions[11]['controller_model_ended_ns']
    def frame_at(ns): return slope*((ns-rows[0]['capture_ns'])/1e9)+intercept
    data={'classification':'posthoc exploratory retrospective analysis','source':{'video_sha256':sha(video),'events_sha256':sha(SRC/'events.jsonl'),'report_sha256':sha(SRC/'report.json')},'method':{'reference_crop_px':[321,180,640,480],'video_crop_px':[0,80,640,480],'comparison_size_px':[160,120],'metric':'mean absolute RGB pixel difference','fps':10.0,'source_playback_speed':2.0,'fit':'ordinary least squares over the best-match frame for each selected screenshot'},'anchors':rows,'fit':{'frame_per_capture_second':slope,'intercept':intercept,'frame_period_ms':1000/(10/2),'rms_residual_frames':math.sqrt(sum(x*x for x in residual)/len(residual)),'max_abs_residual_frames':max(map(abs,residual)),'loo_rms_residual_frames':math.sqrt(sum(x*x for x in loo)/len(loo)),'loo_max_abs_residual_frames':max(map(abs,loo))},'decision_11_timing':{'controller_model_started_ns':model_start_ns,'controller_model_ended_ns':model_end_ns,'accepted_ns':accept,'model_start_frame_estimate':frame_at(model_start_ns),'model_end_frame_estimate':frame_at(model_end_ns),'accept_frame_estimate':frame_at(accept),'sequence_459_capture_frame_estimate':frame_at(observations[459]['capture_ns']),'sequence_504_capture_frame_estimate':frame_at(observations[504]['capture_ns'])},'health_roi_comparison':health,'inference_boundary':{'health_reference':'Decision screenshot 11 (sequence 459) is manually reported as 4%; decision screenshot 12 (sequence 504) shows 0%.','video_hud_transition':'Encoded video crop is compared pixelwise to the two reference HUD regions across frames 647–708.','limits':'Video was encoded at 10 fps and 2x playback, so one frame represents about 200 ms of source control time. The pixel-state change overlaps model completion and action acceptance at this temporal resolution. This cannot order death against those events or identify the damaging cause.'}}
    OUT.write_text(json.dumps(data,indent=2)+'\n')
    print(json.dumps(data['fit'],indent=2)); print([(r['sequence'],r['best_frames'][0]['frame'],r['best_frames'][0]['mae']) for r in rows])
if __name__=='__main__': main()
