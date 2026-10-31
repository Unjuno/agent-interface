from pathlib import Path
from zipfile import ZipFile
import json
here=Path(__file__).resolve().parent
baseline=None
for n,mode in [('r09','wait'),('r10','cancel'),('r11','cancel'),('r12','wait')]:
 with ZipFile(here/(n+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));r=read('output/result.json');a=read('output/action.json');samples=[json.loads(x) for x in z.read('output/samples.jsonl').splitlines()]
  source=z.read('runner.py');baseline=source if baseline is None else baseline
  assert source==baseline and z.read('exit.txt').decode('utf-8-sig').strip()=='0'
  assert r['status']=='completed' and r['task_success'] is None and r['route']==mode and r['action']==a and r['samples']==samples and r['w_down_after'] is False
  assert r['close']['release']['verified'] and next(x for x in samples if x['label']=='before')['ammo']==50
  after=next(x for x in samples if x['label']=='after')
  if mode=='wait':assert a['status']=='withheld' and a['input_dispatched'] is False and all(x['ammo']==50 for x in samples)
  else:
   mon=r['monitor'];ex=a['execution'];release=ex['releases'][0];drop=next(x for x in samples if x['ammo']==49)
   assert mon['held_observed'] and mon['cancel']['status']=='cancel_requested' and mon['cancel']['release_confirmed'] is False
   assert a['status']=='execution_failed' and ex['failed_op_effect'].startswith('unknown') and ex['program_emissions']>0 and not ex['waits'][0]['completed']
   assert release['verified'] and not release['keys_down'] and not release['buttons_down']
   assert mon['held_ns']<mon['cancel_requested_ns']<release['monotonic_ns']<after['host_ns']<drop['host_ns']
   assert after['ammo']==50 and after['tic']<drop['tic'] and samples[-1]['ammo']==49
   print(n,'verified release then 50 -> 49; first observed drop after release ms',round((drop['host_ns']-release['monotonic_ns'])/1e6,3))
for n in ('r02','r03'):
 with ZipFile(here/(n+'.zip')) as z:assert 'explicit query-worker cancellation token required' in json.loads(z.read('output/result.json'))['error']
for n in ('r05','r06','r07','r08'):
 with ZipFile(here/(n+'.zip')) as z:assert 'requires explicit process_identity=True' in json.loads(z.read('output/result.json'))['error']
for n in ('r01','r04'):
 with ZipFile(here/(n+'.zip')) as z:assert json.loads(z.read('output/result.json'))['status']=='completed'
print('all twelve attempts accounted for; controls and cancellation receipts verified')
