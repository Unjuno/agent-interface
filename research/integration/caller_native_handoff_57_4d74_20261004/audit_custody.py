import hashlib, json, pathlib, subprocess
repo = pathlib.Path(__file__).resolve().parent / 'calc-construction-publication-4d74'
def git(*args):
    return subprocess.check_output(['git','-C',str(repo),*args])
roots = ['caller_current_coupling','caller_native_join','motor_native_join','caller_native_state_mapping','native_noinput_units']
errors=[]; rows=[]
for name in roots:
    root=f'research/integration/{name}_57_4d74_20261004'
    manifest=json.loads(git('show',f'HEAD:{root}/FILES.json'))
    for item in manifest['files']:
        data=git('show',f'HEAD:{root}/{item["path"]}')
        if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
            errors.append(root+'/'+item['path'])
    rows.append({'root':root,'literal_members_checked':len(manifest['files'])})
paths=['runtime/core_v1','runtime/backends/x11_v1','runtime/motor_state_v1','research/live_control/adaptive_acquisition_caller_v3.py']
delta=git('diff','--name-only','d744d19de5b4a44f5b6896898eeb25516bbaf481','origin/main','--',*paths).decode().splitlines()
out={'head':git('rev-parse','HEAD').decode().strip(),'main':git('rev-parse','origin/main').decode().strip(),'roots':rows,'errors':errors,'selected_source_changes_since_native_pin':delta,'scope':'Saved Git bytes only; no actors/auditors imported or replayed, no current-main composed execution certificate.'}
target=pathlib.Path(__file__).resolve().parent/'caller-integration-handoff-4d74'
target.mkdir(exist_ok=True)
(target/'CUSTODY.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out));raise SystemExit(bool(errors))
