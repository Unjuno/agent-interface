import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).parent
out=root/'run'
log=(out/'harness.stdout.txt').read_text(encoding='utf-8')
cleanup=json.loads((out/'resource-cleanup.json').read_text(encoding='utf-8'))
cond=json.loads((root/'CONDITIONS.json').read_text(encoding='utf-8-sig'))
pre=json.loads((root/'PREREGISTRATION.json').read_text(encoding='utf-8-sig'))
checks=[]
def check(name,ok): checks.append({'name':name,'passed':bool(ok)})
check('unique_storage_absent_before_start',cond['storage_path_absent_before_start'] is True)
check('session_start_and_termination_receipts',cleanup['started'] is True and cleanup['terminated'] is True)
check('exact_name_filter_scoped_to_new_session','"stage":"exact_name_preflight"' in log and pre['container_name'] in log and pre['session_name'] in log)
check('exact_name_query_empty_success','"exit":0' in log and '"stdout":""' in log and '"stderr":""' in log)
check('parser_failure_before_any_container_or_image',cleanup['cid'] is None and cleanup['pulled'] is False and cleanup['deleted'] is False and cleanup['exit'] is None and 'JsonReaderException' in log)
check('no_test_or_candidate_result',(out/'result.json').exists() is False and not (out/'fake-x-raw').exists())
check('runtime_identity_recorded','"Major":3' in log and '"Minor":0' in log and '"Revision":3' in log)
st=json.loads((root/'STORAGE-CLEANUP-STATUS.json').read_text(encoding='utf-8-sig'))
vhd=pathlib.Path(st['path']); check('isolated_storage_hash_matches',vhd.is_file() and vhd.stat().st_size==st['bytes'] and hashlib.sha256(vhd.read_bytes()).hexdigest()==st['sha256'])
obj={'status':'PASS_SETUP_FAILURE_CLASSIFICATION' if all(x['passed'] for x in checks) else 'FAIL_AUDIT','checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'checks':checks,'scope':'classifies pre-test WSLc harness stop only; no computer-control test ran'}
(root/'AUDIT.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(obj,indent=2))
sys.exit(0 if all(x['passed'] for x in checks) else 1)
