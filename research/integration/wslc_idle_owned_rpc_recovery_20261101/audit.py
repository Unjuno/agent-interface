"""Audit frozen draft source and real-X owned RPC trial records; no -O."""
import hashlib,io,json,subprocess,zipfile
from pathlib import Path
H=lambda b:hashlib.sha256(b).hexdigest()
archive=Path(__file__).with_name('public.zip')
assert H(archive.read_bytes())=='414c424a2557463c81b51e53073d28985aef31a1d0da4eef5eef40133388ab11'
preflight=subprocess.check_output(['git','show','e78ad4102de590f3ad267f6429ae672ec22b3ddf:research/integration/wslc_idle_recovery_preflight_race_20261101/preflight.zip'])
assert H(preflight)=='9ee718018c81f60a2c45101a08bcfd40e44cc8728c377d48d9476951794d57ae'
tree=subprocess.check_output(['git','ls-tree','-r','--full-tree','da3545ad1e1c29d3927573ea2e26dddb5da74303','runtime'],text=True).splitlines()
blobs={r.split('\t',1)[1]:r.split()[2] for r in tree}
def git_blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+bytes([0])+b).hexdigest()
with zipfile.ZipFile(io.BytesIO(preflight)) as prev,zipfile.ZipFile(archive) as z:
 j=lambda n:json.loads(z.read(n).decode('utf-8-sig'))
 m=j('public-manifest.json');assert set(z.namelist())==set(m['files'])|{'public-manifest.json'}
 for n,h in m['files'].items():assert H(z.read(n))==h,n
 frozen=j('trial/manifest.json');c=j('trial/conditions.json')
 assert H(z.read('trial/manifest.json'))==c['manifest_sha256'] and c['allocation']=='idle-owned-real-a01-20261101'
 assert c['draft_head']=='da3545ad1e1c29d3927573ea2e26dddb5da74303'
 for n,h in frozen.items():assert H(z.read(n))==h,n
 assert z.read('target.py')==prev.read('target.py')
 mismatches=[]
 for n in frozen:
  if n.startswith('src/'):
   data=z.read(n).replace(b'\r\n',b'\n');path=n.removeprefix('src/')
   if git_blob(data)!=blobs.get(path):mismatches.append(path)
 assert mismatches==['runtime/host_v1/test_primary_caller.mjs']
 r=j('trial/output/result.json');assert r==j('trial/stdout') and j('trial/launcher-result.json')['returncode']==0
 assert r['status']=='passed' and r['initial_sequence']==1 and r['capture']['status']=='unavailable'
 assert r['state_before_close']=='T' and r['owner_state_after_timeout']=='failed' and r['owner_review_after_timeout']
 old=r['old_close'];assert old['owner_process_retired'] and old['cleanup_status']=='UNKNOWN' and not old['release_attempted'] and not old['release_confirmed']
 assert r['old_pid']!=r['fresh_pid'] and r['mint']['status']=='minted'
 a=r['action'];assert a['status']=='completed' and a['result']['execution']['releases'][-1]['verified']
 assert not a['result']['execution']['releases'][-1]['keys_down'] and not a['result']['execution']['releases'][-1]['buttons_down']
 target=j('trial/output/target-events.json');assert target==r['target_result'] and target['value']=='a'
 assert [(e['type'],e['key']) for e in target['events']]==[('press','a'),('release','a')]
 assert r['fresh_close']['verified'] and r['fresh_close']['release_confirmed'] and r['input_neutral_before_after']
 assert r['target_exit']==r['server_exit']==0
 e={x['name']:x['ns'] for x in r['events']};deadline=r['deadline_ns']
 assert e['stop_sent']<=e['stop_observed']<=e['capture_started']<=e['rpc_pending_while_stopped']<deadline<=e['capture_returned']<=e['old_close_returned']<=e['resumed']<target['events'][0]['host_ns']<=target['events'][1]['host_ns']<=e['fresh_closed']
 print(json.dumps({'status':'audited','deadline_overrun_ms':(e['capture_returned']-deadline)/1e6,
  'old_close':'UNKNOWN, no automatic release','fresh_task':'target recorded a press/release and value a',
  'nonmatching_source_files':mismatches},indent=2))
