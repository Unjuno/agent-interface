"""Verify retained Calc recovery trial and its frozen runtime, without extraction."""
import hashlib, json, xml.etree.ElementTree as ET, zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parent
TRIAL='8bd49b8596f2708eb728bafd4d8072b19be26ad48137936ca020a6fa1b86f964'
SOURCE='41071cdd8ae599ec306b0eb73ff2febe66bc8f3f958ae648e99d2291d1d7250a'
SEAL='622048a6d130cd9c41ade0b108322ab0ef49d5798df058c5305456d3551c2423'
def digest(b):return hashlib.sha256(b).hexdigest()
def require(v,msg):
 if not v:raise ValueError(msg)
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
require(digest((ROOT/'trial.zip').read_bytes())==TRIAL,'trial digest differs')
require(digest((ROOT/'runtime-source.zip').read_bytes())==SOURCE,'source digest differs')
with zipfile.ZipFile(ROOT/'trial.zip') as z,zipfile.ZipFile(ROOT/'runtime-source.zip') as source:
 names=z.namelist();require(len(names)==len(set(names)),'duplicate trial member')
 load=lambda name:json.loads(z.read(name))
 require(digest(z.read('seal.json'))==SEAL,'seal mismatch');rows=load('seal.json')['files'];entries={r['path']:r for r in rows}
 require(len(rows)==len(entries) and set(names)==set(entries)|{'seal.json'},'seal inventory mismatch')
 for path,row in entries.items():
  b=z.read(path);require(len(b)==row['bytes'] and digest(b)==row['sha256'],'bad seal '+path)
 reg=load('registration.json')
 for path,row in reg['files'].items():
  b=z.read(path);require(len(b)==row['bytes'] and digest(b)==row['sha256'],'bad input '+path)
 require(len(source.namelist())==len(set(source.namelist())) and set(source.namelist())==set(reg['server_source_files']),'source inventory mismatch')
 for path,row in reg['server_source_files'].items():
  b=source.read(path);require(len(b)==row['bytes'] and digest(b)==row['sha256'],'bad source '+path)
 source_check=json.loads((ROOT/'source-verification.json').read_text(encoding='utf8'))
 for path,row in source_check['files'].items():
  if path!='runtime/distribution_v2/build.py':require(digest(source.read(path))==row['sha256'],'runtime base differs '+path)
 host_check=json.loads((ROOT/'host-source-verification.json').read_text(encoding='utf8'))
 require(host_check['main']=='3cc8b8b2b005320476e733778502fd776c8c25d7' and len(host_check['files'])==6,'host reference differs')
 for row in host_check['files']:require(blob(z.read('host/'+row['path']))==row['blob'],'host blob differs')
 def reply(owner,i,tool):
  r=load(f'output/{owner}-exchange/original-reply-{i}.json');require(r['tool']==tool,'tool mismatch')
  return json.loads(r['result']['content'][0]['text'])
 failure=reply('first',5,'interface_guarded_input');recovery=reply('first',6,'interface_guarded_recover_input');close1=reply('first',7,'interface_close')
 observation=reply('second',1,'interface_guarded_observe');action=reply('second',5,'interface_guarded_input');close2=reply('second',6,'interface_close')
 require(failure['status']=='execution_failed' and failure['session']['recovery_required'] is True,'fault missing')
 e=failure['result']['execution'];require('injected post-press acknowledgement failure' in e['error'] and 'injected one-shot automatic release failure' in e['releases'][-1]['error'],'fault differs')
 release=recovery['release'];require(recovery['status']=='input_recovered' and release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[],'recovery release differs')
 require(recovery['previous_binding_revision']==failure['session']['binding_revision'] and recovery['replay_allowed'] is False,'recovery revision differs')
 require(close1['status']=='closed' and close2['status']=='closed' and close1['session_id']!=close2['session_id'],'owner mismatch')
 require(action['status']=='completed' and action['result']['recovery_required'] is False,'continuation mismatch')
 releases=action['result']['execution']['releases'];require(bool(releases) and all(r['verified'] is True and r['keys_down']==[] and r['buttons_down']==[] for r in releases),'continuation release differs')
 before=load('output/before-recovery.json');require(bool(before['keys_down']),'held key missing')
 for name in ('after-recovery.json','final-neutral.json','final-observed-neutral.json'):
  require(load('output/'+name)=={'keys_down':[],'buttons_mask':0},'neutral state differs '+name)
 for owner,meta in (('first',reply('first',1,'interface_guarded_observe')),('second',observation)):
  require(digest(z.read(f'output/{owner}-exchange/image-1-1.png'))==meta['source']['native']['artifact']['sha256'],'image differs')
 ocr=load('output/ocr.json');require(ocr['text']=='7' and ocr['exit_code']==0 and digest(z.read('output/recovery-formula.png'))==ocr['image_sha256'],'OCR record differs')
 request=load('output/second-exchange/request-5.json');require([x.get('text') for x in request['args'][3] if x.get('op')=='text']==['31'],'continuation text differs')
 ns={'t':'urn:oasis:names:tc:opendocument:xmlns:table:1.0','o':'urn:oasis:names:tc:opendocument:xmlns:office:1.0'}
 saved=z.read('output/saved.fods');cell=ET.fromstring(saved).find('.//t:table/t:table-row/t:table-cell',ns)
 require(cell is not None and cell.get('{'+ns['o']+'}value')=='731' and cell.get('{'+ns['t']+'}formula') is None,'saved cell differs')
 print(json.dumps({'status':'audited','source_files':len(reg['server_source_files']),'observed_partial':'7','continuation_text':'31','saved_a1':731,'saved_sha256':digest(saved),'recovery_release_verified':True,'continuation_release_verified':True,'final_neutral':True,'model_calls':0},sort_keys=True))
