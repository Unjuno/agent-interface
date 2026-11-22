import hashlib,json
from pathlib import Path
import av,numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[4]; PKG=Path(__file__).resolve().parent; RUN=ROOT/"research/doom/results/map01-astra-attempt-v1"
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def mask(image):
 a=np.asarray(image.convert("RGB"),dtype=np.int16); return (a[:,:,0]>100)&(a[:,:,0]-a[:,:,1]>55)&(a[:,:,0]-a[:,:,2]>55)
meta=json.loads((RUN/"video.json").read_text(encoding="utf-8")); data=json.loads((PKG/"TIMELINE.json").read_text(encoding="utf-8")); protocol=json.loads((PKG/"ANALYSIS_PROTOCOL.json").read_text(encoding="utf-8")); checks={}
video=RUN/meta['file']; checks['source_video_sha256']=sha(video)==meta['sha256']; checks['source_video_size']=video.stat().st_size==meta['bytes']
source_manifest=json.loads((PKG/'SOURCE_MANIFEST.json').read_text(encoding='utf-8')); checks['all_source_hashes']=all(sha(ROOT/x['path'])==x['sha256'] and (ROOT/x['path']).stat().st_size==x['bytes'] for x in source_manifest['files'])
masks=[]; count=0
with av.open(str(video)) as c:
 s=c.streams.video[0]; checks['video_metadata']=(s.frames==780 and float(s.average_rate)==10.0 and (s.width,s.height)==(640,560))
 for frame in c.decode(video=0):
  im=frame.to_image().convert('RGB'); masks.append(mask(im.crop((119,485,214,535))))
checks['frame_count']=len(masks)==780
detected=[i for i in range(1,len(masks)) if int(np.logical_xor(masks[i-1],masks[i]).sum())>=100]
annot=data['annotations']; checks['transition_frames']=detected==[r['detected_transition_frame'] for r in annot]==protocol['decision_rule']['expected_transition_frames']
checks['transition_count']=len(detected)==30
checks['manual_endpoint_and_pickup']=annot[0]['health_before_percent']==100 and annot[-1]['health_after_percent']==0 and any(r['delta_percent_points']==24 for r in annot) and [r['health_after_percent'] for r in annot]==protocol['decision_rule']['expected_health_annotations']
checks['crop_hashes']=all(sha(PKG/r['crop'])==r['crop_sha256'] and (Image.open(PKG/r['crop']).size==(95,50)) for r in annot)
events=[json.loads(line) for line in (RUN/"events.jsonl").read_text(encoding="utf-8").splitlines()]; report=json.loads((RUN/"report.json").read_text(encoding="utf-8")); base=next(e["emit_ns"] for e in events if e.get("event")=="ready"); submits={e["command"]["id"]:e["command"] for e in events if e.get("event")=="command" and e.get("command",{}).get("op")=="submit"}; expected_windows=[]
for i,d in enumerate(report["decisions"]):
 c=submits[f"cover-{i}"]; mode="active_hold" if any(z.get("op")=="hold" for z in c.get("steps",[])) else "coast"; expected_windows.append({'index':i,'start_source_seconds':(d['controller_model_started_ns']-base)/1e9,'end_source_seconds':(d['controller_model_ended_ns']-base)/1e9,'cover_mode':mode})
checks['model_windows']=len(expected_windows)==len(data['model_windows']) and all(a['index']==b['index'] and abs(a['start_source_seconds']-b['start_source_seconds'])<1e-9 and abs(a['end_source_seconds']-b['end_source_seconds'])<1e-9 and a['cover_mode']==b['cover_mode'] for a,b in zip(expected_windows,data['model_windows']))
raw_analysis=json.loads((RUN/"failure-analysis-v1.json").read_text(encoding="utf-8")); expected_decisions=raw_analysis['visual_transcription']['health']; checks['decision_frame_health_reference']=data['decision_frame_health_reference']==expected_decisions
checks['decision_values_present_in_video_states']=set(expected_decisions).issubset({annot[0]['health_before_percent'],*[r['health_after_percent'] for r in annot]})
checks['model_mode_totals']=data['gross_health_point_loss_by_window']=={'active_hold_inference':13,'coast_inference':100,'no_model_call_pending':11}
# Check the documented ROI transform against exact retained screenshot pixels.
cal=json.loads((PKG/"CROP_CALIBRATION.json").read_text(encoding="utf-8")); frame_manifest=json.loads((RUN/"frame-manifest.json").read_text(encoding="utf-8")); frame10=RUN/"frames/10.png"; expected_frame10=next(x["sha256"] for x in frame_manifest if x["file"]=="frames/10.png")
checks['calibration_frame_hash']=sha(frame10)==expected_frame10==cal['source_capture_sha256']
with av.open(str(video)) as c:
 sample=next(f.to_image().convert('RGB') for i,f in enumerate(c.decode(video=0)) if i==cal['video_frame_index'])
source=Image.open(frame10).convert('RGB'); sw=source.crop((321,180,961,660)); vw=sample.crop((0,80,640,560)); sr=source.crop((440,585,535,635)); vr=sample.crop((119,485,214,535))
window_mae=float(np.abs(np.asarray(sw,dtype=np.int16)-np.asarray(vw,dtype=np.int16)).mean()); roi_mae=float(np.abs(np.asarray(sr,dtype=np.int16)-np.asarray(vr,dtype=np.int16)).mean())
def red_count(image):
 a=np.asarray(image.convert('RGB'),dtype=np.int16); return int(((a[:,:,0]>100)&(a[:,:,0]-a[:,:,1]>55)&(a[:,:,0]-a[:,:,2]>55)).sum())
checks['calibration_pixel_match']=abs(window_mae-cal['alignment_check']['source_window_to_video_frame_rgb_mean_absolute_error'])<1e-9 and abs(roi_mae-cal['alignment_check']['source_health_roi_to_video_frame_rgb_mean_absolute_error'])<1e-9 and red_count(sr)==red_count(vr)==990
failed=json.loads((PKG/'ATTEMPT_01.json').read_text(encoding='utf-8')); checks['attempt01_crops_preserved']=all(sha(PKG/'ATTEMPT_01'/x['path'])==x['sha256'] for x in failed['partial_crop_files'])

checks['scope_limited']=all(x in (PKG/'README.md').read_text(encoding='utf-8') for x in ['post-hoc','not causal','no live'])
audit={'schema':'map01-astra-video-health-timeline-audit-v1','checks':checks,'pass':all(checks.values()),'scope':'source hash, exact video transitions and crop integrity; health numerals were manually transcribed'}
(PKG/'AUDIT.json').write_text(json.dumps(audit,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print('PASS_VIDEO_HEALTH_TIMELINE_AUDIT' if audit['pass'] else 'FAIL_VIDEO_HEALTH_TIMELINE_AUDIT');print(json.dumps(audit,indent=2,sort_keys=True))
if not audit['pass']: raise SystemExit(1)
