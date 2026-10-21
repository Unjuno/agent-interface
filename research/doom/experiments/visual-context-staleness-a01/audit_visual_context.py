import hashlib,json,pathlib,re,sys
root=pathlib.Path(__file__).resolve().parent;freeze=json.loads((root/'FREEZE.json').read_text(encoding='utf-8-sig'));errors=[]
def check(v,m):
 if not v:errors.append(m)
def blob(b):return hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()
for name,s in freeze['sources'].items():
 b=(root/name).read_bytes();check(len(b)==s['bytes'],name+' length');check(hashlib.sha256(b).hexdigest()==s['sha256'],name+' sha');check(blob(b)==s['git_blob'],name+' blob')
for name,s in freeze['inputs'].items():
 b=(root/'inputs'/name).read_bytes();check(len(b)==s['bytes'],name+' length');check(hashlib.sha256(b).hexdigest()==s['sha256'],name+' sha');check(blob(b)==s['git_blob'],name+' blob')
check(hashlib.sha256((root/'test_visual_context_staleness.py').read_bytes()).hexdigest()==freeze['test_sha256'],'test freeze')
check(hashlib.sha256((root/'Containerfile').read_bytes()).hexdigest()==freeze['containerfile_sha256'],'container freeze')
check(hashlib.sha256((root/'inputs/fixture.json').read_bytes()).hexdigest()==freeze['fixture_sha256'],'fixture freeze')
check(hashlib.sha256((root/'inputs/frame-audit.json').read_bytes()).hexdigest()==freeze['frame_audit_sha256'],'frame audit freeze')
fixture=json.loads((root/'inputs/fixture.json').read_text(encoding='utf-8-sig'));rows=[json.loads(x) for x in (root/'inputs/events.jsonl').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
for seq in ('2','3'):
 for typ in ('typed_observation','observation'):
  expected=fixture['pair'][seq][typ];check(expected in rows,f'fixture row absent: {seq}/{typ}')
fa=json.loads((root/'inputs/frame-audit.json').read_text(encoding='utf-8-sig'))
for seq in ('2','3'):
 item=fixture['pair'][seq]['typed_observation'];name=pathlib.PurePosixPath(fixture['pair'][seq]['observation']['image']).name;check(fa['frames'][name]['decoded_rgb_sha256']==item['frame_rgb_sha256'],f'{seq}: decoded/event pixel hash mismatch')
raw=(root/'results/wslc.stdout.txt').read_text(encoding='utf-8-sig');check((root/'results/exit.txt').read_text().strip()=='0','WSLc exit');check('Ran 2 tests' in raw and re.search(r'(?m)^OK\r?$',raw) is not None,'WSLc unittest summary')
results=json.loads((root/'results/result.json').read_text(encoding='utf-8-sig'))
for arm in ('changed','control'):
 r=results[arm];check(r['monitor_invalidation'] is None and r['answer_eligible'] is True,f'{arm}: monitor/turn mismatch');check(r['final_status']=='READY_FOR_FRESH_EXECUTOR_ADMISSION',arm+': status');check(r['executor_admission'] is None and r['input_authority_admitted'] is False,arm+': authority')
check(results['changed']['source_frame_rgb_sha256']!=results['changed']['current_frame_rgb_sha256'],'changed frame not distinct')
check(results['changed']['source_health_ammo']==results['changed']['current_health_ammo']==[97,48],'changed arm typed values differ')
check(results['control']['source_frame_rgb_sha256']==results['control']['current_frame_rgb_sha256'],'control frame hashes differ')
if errors:print('\n'.join(errors));sys.exit(1)
print('AUDIT_OK: frozen current-main blobs, retained raw event rows, PNG file/frame digests, one WSLc transcript, both outcomes and authority limits verified')
