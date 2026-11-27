from pathlib import Path
from zipfile import ZipFile
import json
here=Path(__file__).resolve().parent
baseline=None
for n,mode in [('aa01','normal'),('aa02','grab'),('aa03','short'),('aa04','short'),('aa05','grab'),('aa06','normal')]:
 with ZipFile(here/(n+'.zip')) as z:
  r=json.loads(z.read('output/result.json'));src=z.read('runner.py');baseline=src if baseline is None else baseline
  assert src==baseline and z.read('exit.txt').decode('utf-8-sig').strip()=='0' and z.read('condition.txt').decode('utf-8-sig').strip()==mode
  assert r['mode']==mode and r['status']=='completed' and r['down_during'] is True and r['down_after'] is False
  s=r['samples'];e=r['events'];assert len(s)==17 and s[0]['label']=='before' and s[1]['label']=='after' and s[0]['ammo']==50 and all(a['tic']<b['tic'] for a,b in zip(s,s[1:]))
  assert s[0]['host_ns']<e['press_requested_ns']<e['press_confirmed_ns']<e['release_requested_ns']<e['release_confirmed_ns']<s[1]['host_ns'] and 'emergency_release_ns' not in e
  assert 85_000_000<=e['release_requested_ns']-e['press_confirmed_ns']<500_000_000
  if mode=='grab':assert e['grab_confirmed_ns']<e['press_requested_ns'] and e['release_confirmed_ns']<e['ungrab_confirmed_ns']<s[1]['host_ns'] and all(x['ammo']==50 for x in s)
  elif mode=='short':assert e['grab_confirmed_ns']<e['press_requested_ns']<e['press_confirmed_ns']<e['ungrab_confirmed_ns']<e['release_requested_ns'] and r['down_after_ungrab'] is True and s[-1]['ammo']==49
  else:assert 'grab_confirmed_ns' not in e and s[-1]['ammo']==49
  print(n,mode,'ammo',s[0]['ammo'],'->',s[-1]['ammo'],'grab_ms',round((e['ungrab_confirmed_ns']-e['grab_confirmed_ns'])/1e6,3) if mode!='normal' else None)
print('six fixed-order controls, event ordering and input releases verified')
