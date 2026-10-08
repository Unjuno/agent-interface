import hashlib, importlib.metadata, json, sys
from pathlib import Path
import av, numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[4]
PKG=Path(__file__).resolve().parent
RUN=ROOT/"research/doom/results/map01-astra-attempt-v1"
VIDEO=RUN/"map01-astra-live-01-2x.mp4"
ROI=(119,485,214,535)
ANNOTATIONS=[(235,96),(274,94),(282,87),(285,84),(302,83),(311,77),(318,74),(326,68),(337,67),(357,60),(360,84),(370,78),(385,71),(402,64),(408,57),(413,53),(426,52),(437,49),(495,42),(506,39),(519,32),(532,26),(535,22),(547,21),(557,15),(571,12),(581,11),(606,10),(618,4),(703,0)]
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def redmask(image):
 a=np.asarray(image.convert("RGB"),dtype=np.int16)
 return (a[:,:,0]>100)&(a[:,:,0]-a[:,:,1]>55)&(a[:,:,0]-a[:,:,2]>55)
def main():
 meta=json.loads((RUN/"video.json").read_text(encoding="utf-8"))
 assert sha(VIDEO)==meta["sha256"] and VIDEO.stat().st_size==meta["bytes"]
 decoded=[]; masks=[]
 with av.open(str(VIDEO)) as container:
  stream=container.streams.video[0]
  fps=float(stream.average_rate)
  width,height=stream.width,stream.height
  for frame in container.decode(video=0):
   im=frame.to_image().convert("RGB")
   decoded.append(im); masks.append(redmask(im.crop(ROI)))
 assert len(decoded)==meta["frames"]==780 and fps==meta["fps"]==10 and (width,height)==(640,560)
 detected=[i for i in range(1,len(masks)) if int(np.logical_xor(masks[i-1],masks[i]).sum())>=100]
 assert detected==[i for i,_ in ANNOTATIONS], (detected,[i for i,_ in ANNOTATIONS])
 events=[json.loads(line) for line in (RUN/"events.jsonl").read_text(encoding="utf-8").splitlines()]
 report=json.loads((RUN/"report.json").read_text(encoding="utf-8"))
 base=next(e["emit_ns"] for e in events if e.get("event")=="ready")
 submits={e["command"]["id"]:e["command"] for e in events if e.get("event")=="command" and e.get("command",{}).get("op")=="submit"}
 windows=[]
 for i,d in enumerate(report["decisions"]):
  c=submits[f"cover-{i}"]; mode="active_hold" if any(step.get("op")=="hold" for step in c.get("steps",[])) else "coast"
  windows.append({'index':i,'start_source_seconds':(d['controller_model_started_ns']-base)/1e9,'end_source_seconds':(d['controller_model_ended_ns']-base)/1e9,'cover_mode':mode})
 health=100; rows=[]; crops=[]
 for idx,(f,value) in enumerate(ANNOTATIONS):
  lo=(f-1)/5; hi=f/5; active=[w for w in windows if max(lo,w['start_source_seconds'])<min(hi,w['end_source_seconds'])]
  stable_idx=f+1; crop=decoded[stable_idx].crop(ROI); crop_name=f"transition-crops/{stable_idx:04}.png"; crop_path=PKG/crop_name; crop.save(crop_path)
  after=health; health=value; rows.append({'event':idx+1,'detected_transition_frame':f,'stable_crop_frame':stable_idx,'source_time_interval_seconds':[round(lo,3),round(hi,3)],'health_before_percent':after,'health_after_percent':value,'delta_percent_points':value-after,'model_call_indices':[w['index'] for w in active],'cover_modes':[w['cover_mode'] for w in active],'crop':crop_name,'crop_sha256':sha(crop_path)})
  crops.append((idx+1,lo,hi,value,crop.copy()))
 assert health==0 and len(rows)==30
 gross={"active_hold_inference":0,"coast_inference":0,"no_model_call_pending":0}
 for row in rows:
  mode=(row['cover_modes'][0] if row['cover_modes'] else 'no_model_call_pending'); key={'active_hold':'active_hold_inference','coast':'coast_inference','no_model_call_pending':'no_model_call_pending'}[mode]
  if row['delta_percent_points']<0: gross[key]+= -row['delta_percent_points']
 # Save a readable four-sheet contact set without modifying source frames/video.
 for page in range(3):
  batch=crops[page*10:(page+1)*10]; sheet=Image.new('RGB',(600,850),'white'); draw=ImageDraw.Draw(sheet)
  for j,(n,lo,hi,value,crop) in enumerate(batch):
   x=(j%2)*300; y=(j//2)*170; sheet.paste(crop.resize((285,150),Image.Resampling.NEAREST),(x,y+20)); draw.text((x+3,y+2),f'{n}: {lo:.1f}-{hi:.1f}s  health={value}%',fill='black')
  sheet.save(PKG/f'review-sheet-{page+1}.png',compress_level=9)
 run={'schema':'map01-astra-video-health-timeline-run-v1','source_video':meta['file'],'source_video_sha256':meta['sha256'],'source_run':'map01-astra-attempt-v1','video_frames':len(decoded),'fps':fps,'video_dimensions':[width,height],'source_time_formula':'frame_index / fps * playback_speed; source_time is game/run elapsed shown by the video clock','roi_video_xyxy':list(ROI),'mask_rule':{'r_gt':100,'r_minus_g_gt':55,'r_minus_b_gt':55},'changed_mask_pixels_gte':100,'transition_count':len(rows),'annotations':rows,'model_windows':windows,'gross_health_point_loss_by_window':gross,'decision_frame_health_reference':[100,100,100,100,100,84,84,53,49,22,11,4,0],'decision_reference_source':'failure-analysis-v1.json transcription of 13 exact source frames','limits':'One retained video; manual digit transcription from extracted post-transition crops; values are visible HUD percentages, not independent game state or causal damage labels.'}
 (PKG/'TIMELINE.json').write_text(json.dumps(run,indent=2,sort_keys=True)+'\n',encoding='utf-8')
 raw='\n'.join([f"source_sha256={meta['sha256']}",f"frames={len(decoded)} fps={fps} dimensions={width}x{height}",f"health_transitions={len(rows)}",f"gross_health_point_loss_by_window={json.dumps(gross,sort_keys=True)}",'event time_interval health_before -> health_after model_call cover']+[f"{r['event']:02d} {r['source_time_interval_seconds'][0]:.1f}-{r['source_time_interval_seconds'][1]:.1f}s {r['health_before_percent']}->{r['health_after_percent']} {r['model_call_indices']} {r['cover_modes']}" for r in rows])+'\nPASS_VIDEO_HEALTH_TIMELINE\n'
 (PKG/'RAW_TIMELINE.txt').write_text(raw,encoding='utf-8')
 print(raw,end='')
 print('Pillow='+importlib.metadata.version('Pillow'),'numpy='+np.__version__,'av='+importlib.metadata.version('av'))
if __name__=='__main__': main()
