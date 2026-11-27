"""Audit close-vs-withhold held-key trials and retained source; no -O."""
import hashlib,io,json,subprocess,zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
archive=Path(__file__).with_name('public.zip')
assert H(archive.read_bytes())=='01bd7abe6c2a1003b5af5671578d68f228537f00c2a71f1c50671b626d325509'
prior=subprocess.check_output(['git','show','f429fa73d5673c902c6939bac76a68a66ee48e27:research/integration/wslc_idle_owned_rpc_recovery_20261101/public.zip'])
assert H(prior)=='414c424a2557463c81b51e53073d28985aef31a1d0da4eef5eef40133388ab11'
with zipfile.ZipFile(io.BytesIO(prior)) as prev,zipfile.ZipFile(archive) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('manifest.json');previous=json.loads(prev.read('trial/manifest.json'))
 for n,h in frozen.items():assert H(z.read(n))==h,n
 source=[n for n in frozen if n.startswith('src/')]
 assert set(source)=={n for n in previous if n.startswith('src/')}
 assert all(frozen[n]==previous[n] and H(prev.read(n))==frozen[n] for n in source)
 prior_target=prev.read('target.py').decode();target=z.read('target.py').decode()
 assert prior_target.replace("display.Display(':195')","display.Display(os.environ.get('TEST_DISPLAY',':195'))")==target
 summaries=[]
 for arm,mode in [('hold-a01','close_old'),('hold-a02','withhold_close')]:
  c=j(f'{arm}/conditions.json');r=j(f'{arm}/output/result.json');launch=j(f'{arm}/launcher-result.json')
  assert c['allocation']=='idle-owned-'+arm+'-20261101' and c['mode']==mode
  assert c['order']==['hold-a01:close_old','hold-a02:withhold_close'] and c['manifest_sha256']==H(z.read('manifest.json'))
  assert r==j(f'{arm}/stdout') and launch['returncode']==0 and r['status']=='passed'
  assert r['initial_sequence']==1 and r['capture']['status']=='unavailable' and r['state_before_resume']=='T'
  assert r['owner_after_timeout']==r['owner_after_late_reply']=='failed' and r['review_after_late_reply']
  assert r['down_before'] and r['down_after'] and not r['down_after_release']
  close=r['old_close'];assert close['owner_process_retired'] and close['cleanup_status']=='UNKNOWN' and not close['release_attempted'] and not close['release_confirmed']
  assert not r.get('fallback_release_attempted',False) and r['target_exit']==r['server_exit']==0
  target=j(f'{arm}/output/target-events.json');assert target==r['target_result'] and target['value']=='a'
  assert [(x['type'],x['key']) for x in target['events']]==[('press','a'),('release','a')]
  e={x['name']:x['ns'] for x in r['events']};deadline=r['deadline_ns']
  assert e['stop_sent']<=e['stop_observed']<=e['capture_started']<=e['rpc_pending']<deadline<=e['capture_returned']<=e['resumed']<=e['fresh_press']<=e['hold_observed']<=e['fixture_release']
  if mode=='close_old':assert e['fresh_press']<=e['old_close']<=e['hold_observed']
  else:assert e['fixture_release']<=e['old_close']
  assert e['hold_observed']-e['fresh_press']>=350_000_000
  assert e['resumed']<target['events'][0]['host_ns']<=target['events'][1]['host_ns']
  summaries.append({'arm':arm,'mode':mode,'hold_ms':(e['hold_observed']-e['fresh_press'])/1e6,
                    'down_before':r['down_before'],'down_after':r['down_after'],'up_after_fixture_release':not r['down_after_release']})
 print(json.dumps(summaries,indent=2))
