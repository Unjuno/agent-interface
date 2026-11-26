"""Synthetic closed-loop proof verifies semantic joins, not only hashes."""
import hashlib,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from PIL import Image
from map01_candidate_setup_evidence_v1 import verify_setup_candidate,EvidenceError,digest_file


def write(root,name,value):
 path=root/name;path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(value,sort_keys=True))


def seal(root,passed):
 files={p.relative_to(root).as_posix():{'bytes':p.stat().st_size,'sha256':digest_file(p)}
        for p in root.rglob('*') if p.is_file() and p.name!='seal.json'}
 write(root,'seal.json',{'passed':passed,'complete_service_retirement':True,'files':files})
 return digest_file(root/'seal.json')


def custody(root, registration, runtime, exit_code):
 unit=root.name+'.service'
 (root/'driver.py').write_text('driver');(root/'launcher.py').write_text('launcher')
 options=['UMask=0077','PrivateTmp=yes','PrivateNetwork=yes',
          'RuntimeMaxSec='+('60s' if runtime=='1min' else '30s'),'TimeoutStopSec=5s','KillMode=control-group']
 registration.update(root=str(root),unit=unit,python='/venv/python',unit_options=options,
                     driver_sha256=digest_file(root/'driver.py'),launcher_sha256=digest_file(root/'launcher.py'))
 write(root,'registration.json',registration);reg_sha=digest_file(root/'registration.json')
 before='MainPID=0\nControlGroup=\nId='+unit+'\nLoadState=not-found\nActiveState=inactive\nSubState=dead\n'
 write(root,'claim.json',{'registration_sha256':reg_sha,'unit':unit,'before':{'exit_code':0,'stdout':before}})
 argv=['systemd-run','--user','--wait','--pipe','--collect','--unit='+unit]
 for option in options:argv.extend(('-p',option))
 argv.extend(('/venv/python','-B',str(root/'driver.py'),reg_sha))
 write(root,'launch.json',{'argv':argv})
 group='/user.slice/app.slice/'+unit
 props={'MainPID':'11','Id':unit,'ControlGroup':group,'PrivateTmp':'yes','PrivateNetwork':'yes',
        'KillMode':'control-group','RuntimeMaxUSec':runtime,'TimeoutStopUSec':'5s','UMask':'0077',
        'InvocationID':'123'}
 write(root,'service-active.json',{'properties':props,'initial_pids':[11]})
 write(root,'launcher-outcome.json',{'retired':True,'exit_code':exit_code,'unit':unit,
    'control_group':group,'timed_out':False,'service_after':{'exit_code':0,'stdout':before}})


def fixture(root):
 creation=root/'creation';gui=root/'gui';headless=root/'headless'
 for p in (creation,gui,headless):p.mkdir()
 wad=root/'wad';wad.write_bytes(b'test-wad');wad_sha=digest_file(wad)
 c=creation/'candidate';c.mkdir();(c/'fixture.png').write_bytes(b'save')
 source_image=Image.new('RGB',(640,480));source_image.save(c/'fixture.source.png')
 source_rgb=hashlib.sha256(source_image.tobytes()).hexdigest()
 candidate={'schema':'map01_os_input_fixture_candidate_v1','setup_mode':'fresh_neutral_fixture_setup_v1',
  'qualification':'pending','map':'MAP01','skill':1,'seed':990619,'vizdoom':'1.3.0','iwad_sha256':wad_sha,
  'save_file':'fixture.png','save_sha256':digest_file(c/'fixture.png'),
  'source_frame':'fixture.source.png','source_frame_sha256':digest_file(c/'fixture.source.png'),'episode_tic':529,
  'source_observation':{'event':'observation','id':'fixture-source','step':0,'sequence':37,'capture_ns':3700,'exact':True,
  'frame_rgb_sha256':source_rgb,'pointer_binding':{'focus':11,'surface':11,'geometry':[0,0,640,480]},
  'renewal_owner_id':'owner','input_owner_generation':0,'target_process_identity':{'sequence':37,'surface':11,'digest':'a'*64},
  'target_renewal_window_identity':{'sequence':37,'surface':11,'digest':'b'*64},
  'focus_samples_match':True,'input_focus_before':11,'input_focus_after':11},
  'setup_input_contract':'fixture state reached through the same X11 Executor and recorded OS-input/coast programs; save is setup-only'}
 write(c,'fixture.json',candidate); manifest=c/'fixture.json';manifest_sha=digest_file(manifest)
 steps=[{'op':'coast','duration_ms':5000,'sample_ms':250},{'op':'coast','duration_ms':4768,'sample_ms':250}]
 program_sha=hashlib.sha256(json.dumps(steps,sort_keys=True,separators=(',',':')).encode()).hexdigest()
 release={'verified':True,'keys_down':[],'buttons_down':[],'keys_unknown':[],'key_state_errors':[]}
 def observed(seq, identifier):
  base={**candidate['source_observation'],'id':identifier,'sequence':seq,'capture_ns':seq*100,
        'target_process_identity':{'sequence':seq,'surface':11,'digest':'a'*64},
        'target_renewal_window_identity':{'sequence':seq,'surface':11,'digest':'b'*64}}
  signals={name:{'status':'observed','value':value,'sequence':seq,'capture_ns':seq*100,
                 'binding':base['pointer_binding'],'signal_id':name}
           for name,value in (('health',100),('ammo',50))}
  early={**base,'event':'typed_observation','signals':signals}
  return early,base
 initial=observed(36,'initial');final=observed(37,'fixture-source')
 events=[{'event':'command','command':{'op':'submit','id':'fresh-coast','steps':steps}},
  {'event':'accepted','id':'fresh-coast','program_sha256':program_sha},*initial,
  {'event':'terminal','id':'fresh-coast','status':'completed','steps_completed':2,'release':release},
  {'event':'command','command':{'op':'save_fixture'}},*final,
  {'event':'fixture_saved','source_sequence':37,'save_sha256':candidate['save_sha256'],'episode_tic':529}]
 (creation/'runtime').mkdir();(creation/'runtime/events.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in events))
 custody(creation,{'candidate_manifest':str(manifest),'steps':steps,'program_sha256':program_sha},'1min',0)
 write(creation,'worker-outcome.json',{'candidate_manifest_sha256':manifest_sha,'passed':True,
  'candidate_status':'unqualified','model_calls':0,'input_admissions_observed':0,
  'admission_observation_complete':True,'owner_close_verified':True,'display_retired':True})
 creation_sha=seal(creation,True)
 (headless/'isolated-save.png').write_bytes(b'save')
 h={'disposition':'HOLD','expected_tic':529,'actual_tic_before_any_refresh':528,
    'candidate_save_sha256':candidate['save_sha256'],'model_calls':0,'input_commands':0,'game_close':'returned',
    'init_started_ns':1,'before_sample_started_ns':2,'before_load_tic':1,'load_started_ns':4,
    'load_returned_ns':5,'after_getter_ns':6,'comparison':'HOLD'}
 write(headless,'worker-outcome.json',h)
 write(headless,'load-attempt.json',{'before_load_tic':1,'before_sample_started_ns':2,'recorded_ns':3,
                                   'candidate_save_sha256':candidate['save_sha256']})
 write(headless,'load-returned.json',{'load_started_ns':4,'load_returned_ns':5,'after_getter_ns':6,
                                    'actual_tic_before_any_refresh':528})
 custody(headless,{},'30s',2)
 headless_sha=seal(headless,False)
 def state(tic):return {'tic':tic,'rate':35,'limit':2625,'x11_input_neutral':True,
   'last_action':[0]*9,'dead':False,'finished':False,'timeout':False}
 states=[state(x) for x in (528,530,531,532,603)]
 clock=[{'event':'loaded','state':states[0],'observed_ns':8}]
 for i,(series,side) in enumerate((('immediate','left'),('immediate','right'),('delayed','left'),('delayed','right'))):
  clock.append({'event':'refresh','series':series,'side':side,'requested_tics':1,'update_state':True,
     'before':states[i],'after':states[i+1], 'start_ns':[10,20,30,2_000_000_400][i],
     'end_ns':[11,21,300,2_030_000_300][i]})
 gate={'passed':True,'validated_ns':2_030_000_500,'immediate_delta':1,'delayed_delta':71,
       'delayed_elapsed_ns':2_030_000_000}
 clock.append({'event':'gate',**gate});(gui/'gui-load-clock-gate.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in clock))
 def digest_identity(scheme,fields):return hashlib.sha256(json.dumps({'scheme':scheme,**fields},sort_keys=True,separators=(',',':')).encode()).hexdigest()
 identity={'xid':11,'pid':4,'start_ticks':5}
 identity['process_generation']=digest_identity('xres-linux-process-v1',identity)
 identity['process_incarnation']=digest_identity('xres-linux-process-incarnation-v1',{'pid':4,'start_ticks':5})
 target={'focus':11,'surface':11,'geometry':[0,0,640,480],'pid':4,'identity':identity}
 (gui/'isolated-save.png').write_bytes(b'save')
 image=Image.new('RGB',(640,480));image.save(gui/'loaded.png')
 rgb=hashlib.sha256(image.tobytes()).hexdigest();image_sha=digest_file(gui/'loaded.png')
 obs={'before':target,'after':target,'capture_started_ns':2_030_000_501,'capture_ns':2_030_000_502,
      'physical_input_neutral':True,'image_sha256':image_sha,'frame_rgb_sha256':rgb,
      'signals':{'health':{'status':'observed','value':100},'ammo':{'status':'observed','value':50}}}
 write(gui,'gui-observation.json',obs)
 write(gui,'capture-raw.json',{'before':target,'capture_started_ns':obs['capture_started_ns'],'capture_ns':obs['capture_ns'],'image_sha256':image_sha,'frame_rgb_sha256':rgb})
 write(gui,'display-active.json',{'load_window':target,'pids':[11,2,3,4],'xvfb_pid':2,'openbox_pid':3,'keymap_neutral':True,'observed_ns':3})
 write(gui,'display-retired.json',{'pidfds_signaled':{'2':True,'3':True,'4':True},'lock_absent':True,
                                  'xauthority_absent':True,'cgroup_pids':[11]})
 write(gui,'load-attempt.json',{'candidate_save_sha256':candidate['save_sha256'],'before_load_tic':2,'recorded_ns':4})
 returned={'actual_tic_before_any_refresh':528,'load_started_ns':5,'load_returned_ns':6,'after_getter_ns':7}
 write(gui,'load-returned.json',returned)
 custody(gui,{'candidate_root':str(creation),'candidate_seal_sha256':creation_sha,
  'candidate_manifest_sha256':manifest_sha,'candidate_save_sha256':candidate['save_sha256'],
  'source_post_save_tic':529,'expected_tic':528,'input_commands':0,'model_calls':0,
  'headless_root':str(headless),'headless_seal_sha256':headless_sha,'headless_outcome_sha256':digest_file(headless/'worker-outcome.json')},'30s',0)
 write(gui,'worker-outcome.json',{'expected_tic':528,'source_post_save_tic':529,'candidate_save_sha256':candidate['save_sha256'],
  'passed':True,'disposition':'PASS','comparison':'PASS','model_calls':0,'input_commands':0,'game_close':'returned',
  'session_close':'returned','clock_gate':gate,'init_started_ns':1,'before_sample_started_ns':2,'before_load_tic':2,**returned})
 gui_sha=seal(gui,True)
 proof=root/'evidence.json';write(root,'evidence.json',{'schema':'map01_setup_candidate_evidence_v1',
   'creation_root':str(creation),'creation_seal_sha256':creation_sha,'gui_root':str(gui),
   'gui_seal_sha256':gui_sha,'expected_restore_tic':528})
 return manifest,proof,wad,creation,gui,headless


class FakeHud:
 def __init__(self,wad,signal_id):self.wad=wad;self.signal_id=signal_id
 def read_frame(self,obs,frame):return {'status':'observed','value':100 if self.signal_id=='health' else 50,
                                      'wad_sha256':digest_file(self.wad)}


class SyntheticEvidenceTests(unittest.TestCase):
 def test_valid_join_and_resealed_missing_process_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=fixture(Path(temp))
   def verify():return verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud):
    self.assertEqual(verify()[2]['expected_restore_tic'],528)
    retired=json.loads((gui/'display-retired.json').read_text());retired['pidfds_signaled'].pop('4')
    write(gui,'display-retired.json',retired);newseal=seal(gui,True)
    spec=json.loads(proof.read_text());spec['gui_seal_sha256']=newseal;proof.write_text(json.dumps(spec))
    with self.assertRaises(EvidenceError):verify()

 def test_resealed_different_loaded_save_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=fixture(Path(temp))
   (gui/'isolated-save.png').write_bytes(b'other')
   spec=json.loads(proof.read_text());spec['gui_seal_sha256']=seal(gui,True);proof.write_text(json.dumps(spec))
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud),self.assertRaises(EvidenceError):
    verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)
 def test_resealed_shifted_gate_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=fixture(Path(temp))
   path=gui/'gui-load-clock-gate.jsonl';rows=[json.loads(line) for line in path.read_text().splitlines()]
   for row in rows[1:5]:row['start_ns']+=10_000_000_000;row['end_ns']+=10_000_000_000
   path.write_text(''.join(json.dumps(row)+'\n' for row in rows))
   spec=json.loads(proof.read_text());spec['gui_seal_sha256']=seal(gui,True);proof.write_text(json.dumps(spec))
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud),self.assertRaises(EvidenceError):
    verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)

 def test_resealed_non_neutral_creation_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=fixture(Path(temp))
   path=creation/'runtime/events.jsonl';events=[json.loads(line) for line in path.read_text().splitlines()]
   steps=[{'op':'hold','keys':['a'],'duration_ms':100}]
   digest=hashlib.sha256(json.dumps(steps,sort_keys=True,separators=(',',':')).encode()).hexdigest()
   events[0]['command']['steps']=steps;events[1]['program_sha256']=digest
   next(row for row in events if row['event']=='terminal')['steps_completed']=1
   path.write_text(''.join(json.dumps(row)+'\n' for row in events))
   reg=json.loads((creation/'registration.json').read_text());reg['steps']=steps;reg['program_sha256']=digest
   custody(creation,reg,'1min',0);creation_sha=seal(creation,True)
   greg=json.loads((gui/'registration.json').read_text());greg['candidate_seal_sha256']=creation_sha
   custody(gui,greg,'30s',0);gui_sha=seal(gui,True)
   spec=json.loads(proof.read_text());spec.update(creation_seal_sha256=creation_sha,gui_seal_sha256=gui_sha)
   proof.write_text(json.dumps(spec))
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud),self.assertRaises(EvidenceError):
    verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)
 def test_resealed_mismatching_save_receipt_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=fixture(Path(temp))
   path=creation/'runtime/events.jsonl';events=[json.loads(line) for line in path.read_text().splitlines()]
   events[-1]['episode_tic']=528;path.write_text(''.join(json.dumps(row)+'\n' for row in events))
   creation_sha=seal(creation,True)
   greg=json.loads((gui/'registration.json').read_text());greg['candidate_seal_sha256']=creation_sha
   custody(gui,greg,'30s',0);gui_sha=seal(gui,True)
   spec=json.loads(proof.read_text());spec.update(creation_seal_sha256=creation_sha,gui_seal_sha256=gui_sha)
   proof.write_text(json.dumps(spec))
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud),self.assertRaises(EvidenceError):
    verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)
 def test_wrong_seed_and_timeout_are_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=fixture(Path(temp))
   for seed,timeout in ((990618,75),(990619,600)):
    with self.subTest(seed=seed,timeout=timeout),patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud),self.assertRaises(EvidenceError):
     verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,seed,timeout,wad)

 def test_missing_setup_contract_is_rejected_even_if_resealed(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=fixture(Path(temp))
   data=json.loads(manifest.read_text());data.pop('setup_input_contract');manifest.write_text(json.dumps(data))
   manifest_sha=digest_file(manifest)
   worker=json.loads((creation/'worker-outcome.json').read_text());worker['candidate_manifest_sha256']=manifest_sha
   write(creation,'worker-outcome.json',worker);creation_sha=seal(creation,True)
   greg=json.loads((gui/'registration.json').read_text());greg['candidate_seal_sha256']=creation_sha;greg['candidate_manifest_sha256']=manifest_sha
   custody(gui,greg,'30s',0);gui_sha=seal(gui,True)
   spec=json.loads(proof.read_text());spec.update(creation_seal_sha256=creation_sha,gui_seal_sha256=gui_sha)
   proof.write_text(json.dumps(spec))
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud),self.assertRaises(EvidenceError):
    verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)

 def test_resealed_unisolated_service_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=fixture(Path(temp))
   active=json.loads((gui/'service-active.json').read_text());active['properties']['PrivateTmp']='no'
   write(gui,'service-active.json',active);gui_sha=seal(gui,True)
   spec=json.loads(proof.read_text());spec['gui_seal_sha256']=gui_sha;proof.write_text(json.dumps(spec))
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud),self.assertRaises(EvidenceError):
    verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)

 def test_resealed_missing_intermediate_full_frame_is_rejected(self):
  with tempfile.TemporaryDirectory() as temp:
   manifest,proof,wad,creation,gui,headless=fixture(Path(temp))
   path=creation/'runtime/events.jsonl';events=[json.loads(line) for line in path.read_text().splitlines()]
   events=[row for row in events if not (row.get('event')=='observation' and row.get('id')=='initial')]
   path.write_text(''.join(json.dumps(row)+'\n' for row in events));creation_sha=seal(creation,True)
   greg=json.loads((gui/'registration.json').read_text());greg['candidate_seal_sha256']=creation_sha
   custody(gui,greg,'30s',0);gui_sha=seal(gui,True)
   spec=json.loads(proof.read_text());spec.update(creation_seal_sha256=creation_sha,gui_seal_sha256=gui_sha)
   proof.write_text(json.dumps(spec))
   with patch('doom_hud_signal_v3.DoomStatusNumberReader',FakeHud),self.assertRaises(EvidenceError):
    verify_setup_candidate(manifest,proof,digest_file(proof),'1.3.0',digest_file(wad),1,990619,75,wad)

if __name__=='__main__':unittest.main()
