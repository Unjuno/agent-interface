import pathlib,sys,os,json,time,hashlib,importlib.util
from PIL import Image
from Xlib import X,XK,display

root=pathlib.Path(sys.argv[1]);ws=root.parent;src=ws/'v39-hud-candidate-source-tru0ui8x';baseline=ws/'map01-v39-import-closure-02-20261127';original=pathlib.Path('/home/user/issue59-v39-clock-preflight-99509a3-xs1mmios');plan=json.loads((root/'registration.json').read_text());manifest=json.loads((src/'SOURCE_MANIFEST.json').read_text())
def check(v,msg):
 if not v:raise ValueError(msg)
check(hashlib.sha256((src/'SOURCE_MANIFEST.json').read_bytes()).hexdigest()==plan['source_manifest_sha256'],'source manifest')
for e in manifest['files']:
 b=(src/e['path']).read_bytes();check(len(b)==e['bytes'] and hashlib.sha256(b).hexdigest()==e['sha256'],'source changed')
sealbytes=(original/'seal.json').read_bytes();check(hashlib.sha256(sealbytes).hexdigest()==plan['original_seal_sha256'],'source seal');seal=json.loads(sealbytes);raw=(original/'runtime/001.png').read_bytes();entry=seal['files']['runtime/001.png'];check(len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],'source frame');wad=src/'_vizdoom/vizdoom/freedoom2.wad'
with wad.open('rb') as f:check(hashlib.file_digest(f,'sha256').hexdigest()==plan['wad_sha256'],'wad')
sys.path[:0]=[str(src/'research/doom'),str(src/'research/live_control'),str(src)]
from doom_hud_signal_v3 import DoomStatusNumberReader
from input_owner_v12 import InputOwner
from lease_release_v1 import Lease
from observable_signal_guard_v2 import ObservableSignalGuard
check(hashlib.sha256((baseline/'research/doom/doom_hud_signal_v1.py').read_bytes()).hexdigest()==plan['baseline_reader_sha256'],'baseline reader changed')
spec=importlib.util.spec_from_file_location('baseline_hud',baseline/'research/doom/doom_hud_signal_v1.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);candidate=DoomStatusNumberReader(wad,signal_id='health');old=module.DoomStatusNumberReader(wad)
conn=display.Display();screen=conn.screen();window=screen.root.create_window(0,0,1280,800,0,screen.root_depth,X.InputOutput,X.CopyFromParent,background_pixel=screen.black_pixel,override_redirect=True,event_mask=X.ExposureMask|X.KeyPressMask|X.KeyReleaseMask);gc=window.create_gc();owner=None;lease=None;result={'schema':'hud-occlusion-xvfb-live-v1','model_calls':0,'game_started':False,'input_target':'owned synthetic Xvfb window','success':False};events=[]
try:
 window.map();window.set_input_focus(X.RevertToParent,X.CurrentTime);conn.sync()
 with Image.open(original/'runtime/001.png') as im:frame=im.convert('RGB')
 for y in range(0,800,20):
  chunk=frame.crop((0,y,1280,min(y+20,800)));window.put_image(gc,0,y,1280,chunk.height,X.ZPixmap,screen.root_depth,0,chunk.tobytes('raw','BGRX'))
 conn.sync()
 def capture(sequence,name):
  raw=window.get_image(0,0,1280,800,X.ZPixmap,0xffffffff);img=Image.frombytes('RGB',(1280,800),raw.data,'raw','BGRX');img.save(root/name);stamp=time.perf_counter_ns();obs={'sequence':sequence,'capture_ns':stamp,'pointer_binding':{'focus':window.id,'surface':window.id,'geometry':[321,180,640,480]},'image':str(root/name)};return obs,img
 obs1,img1=capture(1,'clean.png');clean=candidate.read_frame(obs1,img1);check(clean['status']=='observed' and clean['value']==100,'initial read not 100');binding=obs1['pointer_binding'];guard=ObservableSignalGuard({'op':'observable_signal_guard','guard_id':'owned-hud','source_sequence':1,'signal_id':'health','source_value':100,'hard_minimum':80,'max_source_age_ms':10000,'on_soft_change':'preserve_existing_policy','on_hard_change':'needs_decision','on_unknown':'needs_decision'},clean,binding)
 lease=Lease(time.perf_counter_ns()+8_000_000_000);lease.expected_focus=window.id;lease.expected_surface=window.id;owner=InputOwner(os.environ['DISPLAY']);ack=owner.call('down',lease,'w');code=conn.keysym_to_keycode(XK.string_to_keysym('w'));before=conn.query_keymap();down_before=bool(before[code//8] & (1 << (code%8)));check(down_before,'key not down before occlusion')
 gc.change(foreground=screen.black_pixel);window.fill_rectangle(gc,321+102+12,180+411,3,38);conn.sync();obs2,img2=capture(2,'occluded.png');original_read=old.read(obs2);reading=candidate.read_frame(obs2,img2);outcome=guard.evaluate(reading);check(original_read['status']=='observed' and original_read['value']==0,'baseline not exposed');check(reading['status']=='unknown' and outcome['status']=='UNKNOWN' and outcome['requires_new_decision'] is True and outcome['grants_input_authority'] is False,'candidate did not fail closed')
 cancel_ns=time.perf_counter_ns();lease.set();interruption=lease.wait_interruption(2);check(interruption is not None,'release not observed');record=interruption['record'];after=conn.query_keymap();down_after=bool(after[code//8] & (1 << (code%8)));check(record['verified'] is True and not down_after and record['reason']=='cancelled','neutral release not verified')
 result.update(success=True,clean_health=clean['value'],baseline_after={'status':original_read['status'],'value':original_read['value']},candidate_after={'status':reading['status'],'value':reading['value'],'reason':reading.get('reason')},guard={'status':outcome['status'],'requires_new_decision':outcome['requires_new_decision'],'grants_input_authority':outcome['grants_input_authority']},key_down_before=down_before,key_down_after=down_after,release_verified=record['verified'],release_reason=record['reason'],cancel_to_verified_ms=(record['verified_ns']-cancel_ns)/1e6,source_sequence=1,occluded_sequence=2,observation_contract='synthetic screenshot displayed in owned Xvfb window; no live game or model')
 events=[{'event':'key_admission','ack':ack},{'event':'source_signal','signal':clean},{'event':'candidate_signal','signal':reading},{'event':'guard_outcome','outcome':outcome},{'event':'owner_interruption','receipt':interruption}]
finally:
 if lease is not None:lease.set()
 if owner is not None:
  try:owner.close();result['owner_thread_stopped']=owner.stopped.is_set()
  except Exception as e:result['owner_close_error_type']=type(e).__name__
 try:window.destroy();conn.sync();conn.close()
 except Exception as e:result['display_close_error_type']=type(e).__name__
 (root/'result.json').write_text(json.dumps(result,indent=2)+'\n');(root/'events.json').write_text(json.dumps(events,indent=2)+'\n')
print(json.dumps(result),flush=True)
