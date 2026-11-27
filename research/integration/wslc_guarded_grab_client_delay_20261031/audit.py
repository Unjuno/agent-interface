from pathlib import Path
from zipfile import ZipFile
import hashlib,json,statistics
here=Path(__file__).resolve().parent
order=['v01:baseline','v02:grab','v03:grab','v04:baseline','v05:baseline','v06:grab'];measurements={'baseline':[],'grab':[]};source_hash=None
for item in order:
 name,mode=item.split(':')
 with ZipFile(here/(name+'.zip')) as z:
  read=lambda p:json.loads(z.read(p));h=lambda b:hashlib.sha256(b).hexdigest();c=read('conditions.json');r=read('output/result.json');a=r['action']
  assert c['allocation']==name and c['mode']==mode and c['order']==order and c['runner_sha256']==h(z.read('runner.py')) and c['model_calls']==0
  if source_hash is None:source_hash=c['runner_sha256']
  else:assert c['runner_sha256']==source_hash
  assert z.read('container.exit').decode('utf-8-sig').strip()=='0' and r['status']=='completed' and r['model_calls']==0 and r['press_mode']==mode and r['dispatch']=='completed' and a['status']=='completed'
  assert [e['type'] for e in r['events']]==['press','release'] and all(e['keycode']==r['target_keycode'] for e in r['events'])
  rel=a['execution']['releases'];assert rel and all(q['verified'] and not q['keys_down'] and not q['buttons_down'] for q in rel)
  assert r['close']['status']=='closed' and r['close']['release']['verified'] and not r['close']['release']['keys_down'] and not r['close']['release']['buttons_down'] and not r['f_down_after']
  assert not r['damage_events'] and not r['latched'] and not r['damage_latched']
  names=[p for p in z.namelist() if '/owner/' in p and p.endswith(f"/observation-{r['source_sequence']}.json")];assert len(names)==1;source=read(names[0]);assert r['probe_focus_id']==source['pointer_binding']['focus']
  assert r['press_call_started_ns']<r['probe_start_ns']<r['probe_end_ns']
  if mode=='grab':assert r['grab_started_ns']<r['probe_start_ns']<r['grab_ended_ns']<r['probe_end_ns']
  else:assert 'grab_started_ns' not in r
  ms=(r['probe_end_ns']-r['probe_start_ns'])/1e6;measurements[mode].append(ms);print(name,mode,'other_client_query_ms',round(ms,3))
for mode,items in measurements.items():print(mode,'n',len(items),'min/median/max ms',*[round(x,3) for x in (min(items),statistics.median(items),max(items))])
print('grab minus baseline medians ms',round(statistics.median(measurements['grab'])-statistics.median(measurements['baseline']),3))
print('PASS: same runner, query/focus ordering, target input and neutral releases')
