from pathlib import Path
from zipfile import ZipFile
import hashlib,json,statistics
here=Path(__file__).resolve().parent
order=['u01:baseline','u02:grab','u03:grab','u04:baseline','u05:baseline','u06:grab'];measurements={'baseline':[],'grab':[]};source_hash=None
for item in order:
 name,mode=item.split(':')
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json');a=r['action']
  assert c['allocation']==name and c['mode']==mode and c['order']==order and c['runner_sha256']==h(z.read('runner.py')) and c['model_calls']==0
  if source_hash is None:source_hash=c['runner_sha256']
  else:assert c['runner_sha256']==source_hash
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['model_calls']==0 and r['press_mode']==mode and r['dispatch']=='completed' and a['status']=='completed'
  assert [e['type'] for e in r['events']]==['press','release'] and all(e['keycode']==r['target_keycode'] for e in r['events'])
  releases=a['execution']['releases'];assert releases and all(q['verified'] and not q['keys_down'] and not q['buttons_down'] for q in releases)
  assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['f_down_after']
  assert not r['damage_events'] and not r['latched'] and not r['damage_latched']
  checks=[q for q in a['additional_input_checks'] if q['stage']=='before_key_press:f'];assert len(checks)==1 and checks[0]['eligible']
  assert r['press_call_started_ns']<checks[0]['started_ns']<checks[0]['ended_ns']<r['press_call_ended_ns']<=a['execution']['waits'][0]['started_ns']
  ms=(r['press_call_ended_ns']-r['press_call_started_ns'])/1e6
  if mode=='grab':assert r['press_call_started_ns']<r['grab_started_ns']<checks[0]['started_ns']<checks[0]['ended_ns']<r['press_synced_ns']<r['grab_ended_ns']<r['press_call_ended_ns']
  else:assert 'grab_started_ns' not in r
  measurements[mode].append(ms);print(name,mode,'press_call_ms',round(ms,3))
for mode,items in measurements.items():print(mode,'n',len(items),'min/median/max ms',*[round(x,3) for x in (min(items),statistics.median(items),max(items))])
print('grab minus baseline medians ms',round(statistics.median(measurements['grab'])-statistics.median(measurements['baseline']),3))
print('PASS: same runner, guarded check ordering, action, target key events and release')
