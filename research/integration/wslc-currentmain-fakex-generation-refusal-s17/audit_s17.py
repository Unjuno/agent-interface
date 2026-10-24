import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).parent; out=root/'run'; log=(out/'harness.stdout.txt').read_text(encoding='utf-8'); cleanup=json.loads((out/'resource-cleanup.json').read_text()); pre=json.loads((root/'PREREGISTRATION.json').read_text(encoding='utf-8-sig')); cond=json.loads((root/'CONDITIONS.json').read_text(encoding='utf-8-sig'))
checks=[]
def c(n,v):checks.append({'name':n,'passed':bool(v)})
c('unique_path_was_absent',cond['storage_path_absent_before_start'] is True)
c('session_terminated',cleanup['started'] is True and cleanup['terminated'] is True)
c('exact_name_query_scoped',pre['container_name'] in log and pre['session_name'] in log and '"exit":0' in log)
c('empty_query_output_recorded','"stdout":""' in log and '"stderr":""' in log)
c('parse_failure_before_pull_or_create',cleanup['pulled'] is False and cleanup['cid'] is None and cleanup['deleted'] is False and 'JsonReaderException' in log)
c('no_test_raw_or_result',(out/'result.json').exists() is False and not (out/'fake-x-raw').exists())
c('wslc_version_3030','"Major":3' in log and '"Minor":0' in log and '"Revision":3' in log)
s=json.loads((root/'STORAGE-CLEANUP-STATUS.json').read_text(encoding='utf-8-sig')); vp=pathlib.Path(s['path']); c('vhdx_hash_matches',vp.is_file() and vp.stat().st_size==s['bytes'] and hashlib.sha256(vp.read_bytes()).hexdigest()==s['sha256'])
a={'status':'PASS_SETUP_FAILURE_CLASSIFICATION' if all(x['passed'] for x in checks) else 'FAIL_AUDIT','checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'checks':checks,'scope':'pre-test harness stop only; no computer-control test ran'}
(root/'AUDIT.json').write_text(json.dumps(a,indent=2,sort_keys=True)+'\n',encoding='utf-8');print(json.dumps(a,indent=2));sys.exit(0 if all(x['passed'] for x in checks) else 1)
