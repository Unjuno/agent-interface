"""Verify sealed primary recovery evidence without extracting untrusted archive paths."""
import hashlib
import json
from pathlib import Path
import zipfile

ROOT=Path(__file__).resolve().parent
CASES={
 'startup-refusal.zip':('92f1d1d09625ce65d08908009d7da63cf61f56eb270c6783861a88f0362bd816','41fcea1623de7a78fcd2602d3f72fc74b47eae13d83a159a0624dbeadf6d4122'),
 'controlled-recovery.zip':('5ff95c7e652e0c3955d003d5f72412b5095ec2b39758aad6d6a5bf9b57cf7961','5cdf8c9591062c0125d64d75244d4faa43302fa18826531a24c344cf1b3d1123'),
}
def digest(b): return hashlib.sha256(b).hexdigest()
def require(value,message):
 if not value: raise ValueError(message)
def load(z,name):return json.loads(z.read(name))
def git_blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
for name,(archive_hash,seal_hash) in CASES.items():
 require(digest((ROOT/name).read_bytes())==archive_hash,'archive mismatch '+name)
 with zipfile.ZipFile(ROOT/name) as z:
  names=z.namelist();require(len(names)==len(set(names)),'duplicate members')
  require(digest(z.read('seal.json'))==seal_hash,'seal mismatch')
  rows=load(z,'seal.json')['files'];entries={r['path']:r for r in rows}
  require(len(rows)==len(entries) and set(names)==set(entries)|{'seal.json'},'seal inventory mismatch')
  for path,row in entries.items():
   b=z.read(path);require(len(b)==row['bytes'] and digest(b)==row['sha256'],'bad seal '+path)
  registration=load(z,'registration.json')
  for path,row in registration['files'].items():
   b=z.read(path);require(len(b)==row['bytes'] and digest(b)==row['sha256'],'bad registration '+path)
  require(git_blob(z.read('host/primary_caller.mjs'))=='b711066bdda408f4f12ecb4466e07992e6875ba1','tested caller differs')
  outcome=load(z,'output/result.json')
  if name=='startup-refusal.zip':
   require(outcome['passed'] is False and outcome['input_attempted'] is False,'startup classification differs')
   original=load(z,'output/exchange/original-reply-1.json');meta=json.loads(original['result']['content'][0]['text'])
   require(meta['status']=='backend_unavailable' and meta['input_dispatched'] is False,'startup failure differs')
   require(load(z,'output/final-keymap.json')['down'] is False,'startup key down')
  else:
   require(outcome['passed'] is True and outcome['input_attempted'] is True,'success classification differs')
   def reply(i,tool):
    row=load(z,f'output/exchange/original-reply-{i}.json');require(row['tool']==tool,'tool mismatch')
    return row,json.loads(row['result']['content'][0]['text'])
   _,fault=reply(5,'interface_guarded_input');_,recovered=reply(6,'interface_guarded_recover_input');_,closed=reply(8,'interface_close')
   require(fault['status']=='execution_failed' and fault['session']['recovery_required'] is True,'failure mismatch')
   x=fault['result']['execution'];require('injected post-press acknowledgement failure' in x['error'] and 'injected one-shot automatic release failure' in x['releases'][-1]['error'],'fault mismatch')
   release=recovered['release'];require(recovered['status']=='input_recovered' and release['verified'] is True and release['keys_down']==[] and release['buttons_down']==[],'release mismatch')
   require(recovered['previous_binding_revision']==fault['session']['binding_revision'] and recovered['replay_allowed'] is False and recovered['review_required'] is True,'revision mismatch')
   before=load(z,'output/before.json');after=load(z,'output/after.json')
   require(before['down'] is True and after['down'] is False and before['keycode']==after['keycode'],'keymap mismatch')
   require([e['type'] for e in before['events']]==[2] and [e['type'] for e in after['events']]==[2,3],'event mismatch')
   refusal=load(z,'output/line-08.json');require(refusal['status']=='command_error' and refusal['replay_allowed'] is False and closed['status']=='closed','caller stop mismatch')
   require(load(z,'output/final-keymap.json')['down'] is False,'final key down')
  print(json.dumps({'archive':name,'status':'audited','input_attempted':outcome['input_attempted'],'passed':outcome['passed']},sort_keys=True))
