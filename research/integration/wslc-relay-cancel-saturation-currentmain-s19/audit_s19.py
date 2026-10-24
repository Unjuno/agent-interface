import hashlib,json,pathlib,sys
root=pathlib.Path(__file__).parent
run=root/'run'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
pre=read(root/'PREREGISTRATION.json'); inp=read(root/'INPUT-PREFLIGHT.json'); result=read(run/'result.json'); cleanup=read(run/'resource-cleanup.json'); storage=read(root/'STORAGE-CLEANUP-STATUS.json')
events=[json.loads(x) for x in (run/'host-harness.log').read_text(encoding='utf-8-sig').splitlines() if x.strip()]
stages={x['stage']:x.get('details',{}) for x in events}
checks=[]
def check(name,ok):checks.append({'name':name,'passed':bool(ok)})
check('current_main_and_source_identity_pinned',pre['source_commit']=='7b9383077f8f98873eab5eac70b13005c8d2138f' and all(x['matches_origin_main'] for x in pre['critical_sources']))
check('input_preflight_passed',inp['status']=='PASS_INPUT_PREFLIGHT' and inp['wheel_count']==31 and all(x['matches_manifest'] for x in inp['wheel_files']))
check('wslc_version_and_new_session',stages.get('version',{}).get('Major')==3 and stages.get('version',{}).get('Minor')==0 and stages.get('version',{}).get('Revision')==3 and cleanup['started'] and cleanup['terminated'])
check('exact_generated_name_only_preflight',stages.get('exact_name_preflight',{}).get('filter')=='name='+pre['container_name'] and stages['exact_name_preflight'].get('exit')==0 and stages['exact_name_preflight'].get('stdout')=='' and stages['exact_name_preflight'].get('stderr')=='')
check('pinned_image_and_one_offline_container',cleanup['pulled'] and cleanup['imageDeleted'] and cleanup['cid'] and cleanup['deleted'] and cleanup['containerName']==pre['container_name'] and cleanup['exit']==70)
check('offline_install_failure_captured',result['stage']=='offline_install' and result['exit_code']==1 and 'requirements-cp312.lock' in (run/'pip-install.stderr.txt').read_text(encoding='utf-8'))
check('test_body_and_fake_x_not_started',not (run/'test.stdout.txt').exists() and not (run/'test.stderr.txt').exists() and not (run/'raw').exists() and result['status']=='FAIL_OR_UNKNOWN')
check('session_storage_hash_matches',pathlib.Path(storage['path']).is_file() and pathlib.Path(storage['path']).stat().st_size==storage['bytes'] and hashlib.sha256(pathlib.Path(storage['path']).read_bytes()).hexdigest()==storage['sha256'] and storage['session_terminated'] and storage['container_deleted'] and storage['image_deleted'])
rows=[]
for f in sorted(x for x in run.rglob('*') if x.is_file() and x.name!='PRESERVED-RUN-MANIFEST.json'):rows.append({'path':f.relative_to(run).as_posix(),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(run/'PRESERVED-RUN-MANIFEST.json').write_text(json.dumps(rows,indent=2,sort_keys=True)+'\n',encoding='utf-8')
obj={'status':'PASS_SETUP_FAILURE_CLASSIFICATION' if all(x['passed'] for x in checks) else 'FAIL_AUDIT','checks_passed':sum(x['passed'] for x in checks),'checks_total':len(checks),'checks':checks,'scope':'S19 pre-test runner path failure; no computer-control test ran','preserved_run_files':len(rows)}
(root/'AUDIT.json').write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps(obj,indent=2));sys.exit(0 if all(x['passed'] for x in checks) else 1)

