#!/usr/bin/env python3
"""Independent raw-result audit for Issue #2624. Does not import study.py."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path

JAR_SHA="7f210295dfffb4c17b582b27bab41f4dde83f557f00f0877572fdac943f40539"
SAVE_SHA="8fff67b0c130ee59a3838c92754b73225a506902bd4838dcc3f1fb5be286cbed"
MOD_SHA="4b8e413ab0c4561c82edd8e422c517b631f1baee79a0b008adb42e9624965e05"
JS_SHA="7b5bd06bc34db9655e3946a9c202948cdaa0a4b233e0eec1fe063aa8358c220f"
EXPECTED_OUTCOME="PASS_MINDUSTRY_PREMOUNTED_LIVE_SMOKE_SCOPED"

def exact_int(value, expected):
 return type(value) is int and value == expected

def sha(p):
 h=hashlib.sha256();
 with p.open('rb') as f:
  for c in iter(lambda:f.read(1024*1024),b''):h.update(c)
 return h.hexdigest()

def audit(root: Path):
 e=[]
 required=['RESULT.json','asset_manifest.json','acquisition.txt','ready.txt','oracle.json','windows.txt','mindustry.stdout.txt','mindustry.stderr.txt','xvfb.stdout.txt','xvfb.stderr.txt','openbox.stdout.txt','openbox.stderr.txt']
 for n in required:
  if not (root/n).is_file():e.append('missing:'+n)
 if e:return {'passed':False,'errors':e}
 r=json.loads((root/'RESULT.json').read_text())
 a=json.loads((root/'asset_manifest.json').read_text())
 o=json.loads((root/'oracle.json').read_text())
 checks={
  'formal_once': exact_int(r.get('formal_invocations'),1),
  'outcome': r.get('outcome')==EXPECTED_OUTCOME,
  'jar': exact_int(a.get('jar',{}).get('bytes'),87022576) and a.get('jar',{}).get('sha256')==JAR_SHA,
  'save': a.get('save',{}).get('sha256')==SAVE_SHA and a.get('save',{}).get('git_blob')=='7663b25633d853a257fbb407723fe85579120111',
  'mod': a.get('mod_json',{}).get('sha256')==MOD_SHA and a.get('mod_json',{}).get('git_blob')=='137ae8036b7864af744565bbc1c2af566290ea92',
  'js': a.get('main_js',{}).get('sha256')==JS_SHA and a.get('main_js',{}).get('git_blob')=='84e9a0c291d5b7f454d6092f2c100728a9a16da2',
  'acquisition_binding': 'jar_asset_id=559668837' in (root/'acquisition.txt').read_text() and JAR_SHA in (root/'acquisition.txt').read_text(),
  'ready': r.get('ready') is True and (root/'ready.txt').read_text()=='ready',
  'window': r.get('mindustry_window') is True and 'mindustry' in (root/'windows.txt').read_text().lower(),
  'oracle_scalar': exact_int(o.get('width'),300) and exact_int(o.get('height'),250) and o.get('paused') is True and o.get('core_present') is True and exact_int(o.get('copper'),200),
  'oracle_shape': isinstance(o.get('tiles'),list) and len(o['tiles'])==250 and all(isinstance(row,list) and len(row)==300 for row in o['tiles']),
  'zero_authority': all(exact_int(r.get(k),0) for k in ('model_calls','provider_calls','controller_calls','task_input_calls')), 
  'neutral': r.get('pre_input_state',{}).get('neutral') is True and r.get('pre_cleanup_input_state',{}).get('neutral') is True,
  'cleanup': r.get('all_owned_processes_exited') is True and r.get('x_socket_absent_after_cleanup') is True and r.get('mindustry',{}).get('forced_kill') is False and not r.get('forced_kill_records'),
  'ordering': all(type(r.get(k)) is int for k in ('started_ns','ready_ns','finished_ns')) and r['started_ns']<r['ready_ns']<r['finished_ns'],
 }
 e += [k for k,v in checks.items() if not v]
 hashes={n:sha(root/n) for n in required}
 return {'passed':not e,'errors':e,'checks':checks,'file_sha256':hashes,'outcome':r.get('outcome')}

def main():
 ap=argparse.ArgumentParser();ap.add_argument('root',type=Path);ap.add_argument('--out',type=Path);a=ap.parse_args()
 res=audit(a.root)
 if a.out:a.out.write_text(json.dumps(res,indent=2,sort_keys=True)+'\n')
 print(json.dumps(res,sort_keys=True));return 0 if res['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
