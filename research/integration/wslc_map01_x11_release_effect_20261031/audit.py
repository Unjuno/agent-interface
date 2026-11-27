from pathlib import Path
from zipfile import ZipFile
import json,hashlib
here=Path(__file__).resolve().parent
baseline=None
for n,mode in [('q09','wait'),('q10','attack'),('q11','attack'),('q12','wait')]:
 with ZipFile(here/(n+'.zip')) as z:
  read=lambda p:json.loads(z.read(p))
  r=read('output/result.json');a=read('output/action.json');samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
  source=z.read('runner.py');baseline=source if baseline is None else baseline
  assert source==baseline and z.read('exit.txt').decode('utf-8-sig').strip()=='0'
  assert r['status']=='completed' and r['task_success'] is None and r['route']==mode and r['action']==a and r['samples']==samples
  assert all(x['ammo']==50 for x in samples if x['label']=='before') and r['w_down_after'] is False
  assert r['close']['release']['verified']
  after=next(x for x in samples if x['label']=='after')
  if mode=='wait':
   assert a['status']=='withheld' and a['input_dispatched'] is False and all(x['ammo']==50 for x in samples)
  else:
   release=a['execution']['releases'][0];drop=next(x for x in samples if x['ammo']==49)
   assert a['status']=='completed' and release['verified'] and not release['keys_down'] and not release['buttons_down']
   assert release['monotonic_ns'] < after['host_ns'] <= drop['host_ns'] and samples[-1]['ammo']==49
   if n=='q10': assert after['ammo']==50 and after['tic']<drop['tic']
   if n=='q11': assert after['ammo']==49
  print(n,mode,'after',after['ammo'],'last',samples[-1]['ammo'])
for n in ('q01','q02','q03','q04'):
 with ZipFile(here/(n+'.zip')) as z: assert z.read('exit.txt').decode().strip()=='1' and b"No module named 'runtime'" in z.read('raw.log')
for n in ('q05','q08'):
 with ZipFile(here/(n+'.zip')) as z: assert json.loads(z.read('output/result.json'))['status']=='error' and b'requires explicit keyboard input' in z.read('output/traceback.txt')
for n in ('q06','q07'):
 with ZipFile(here/(n+'.zip')) as z:
  r=json.loads(z.read('output/result.json')); release=r['action']['execution']['releases'][0]; after=next(x for x in r['samples'] if x['label']=='after');drop=next(x for x in r['samples'] if x['ammo']==49)
  assert r['status']=='completed' and release['verified'] and release['monotonic_ns']<after['host_ns']<drop['host_ns'] and after['ammo']==50
print('all attempts accounted for; releases and sampled ammunition verified')
