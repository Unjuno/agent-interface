import hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def validate_case(row,r):
    clicks=[x['target'] for x in r['fixture_clicks']]
    expected_g=4 if row['replace'] or row['capacity']==1 else 2
    errs=[]
    if r['capacity']!=row['capacity'] or bool(r['replace'])!=bool(row['replace']):errs.append('condition')
    if clicks!=row['sequence']:errs.append('click_sequence')
    if r['groundings']!=expected_g:errs.append('groundings')
    if r['reuses']!=(2 if (not row['replace'] and row['capacity']==2) else 0):errs.append('reuses')
    if not r['terminal_button_neutral']:errs.append('terminal_button')
    if len(r['steps'])!=4 or [x['target'] for x in r['steps']]!=row['sequence']:errs.append('steps')
    if row['replace']:
        if not r['old_probes']:errs.append('missing_old_probe')
        if any(x['status']!='SCOPE_MISMATCH' or x['eligible'] for x in r['old_probes']):errs.append('old_probe')
        surfaces=[x['surface'] for x in r['steps']]
        if not (surfaces[0]==surfaces[1] and surfaces[2]==surfaces[3] and surfaces[0]!=surfaces[2]):errs.append('surface_transition')
    else:
        if r['old_probes']:errs.append('unexpected_old_probe')
        if len({x['surface'] for x in r['steps']})!=1:errs.append('stable_surface')
    return errs

def main():
    receipt=ROOT/'FORMAL_INVOCATION.json'
    resultp=ROOT/'FORMAL_RESULT.json'
    if receipt.exists() or resultp.exists():raise SystemExit('formal already consumed')
    schedule=json.loads((ROOT/'schedule.json').read_text())
    for row in schedule['rows']:
        if Path(f"/tmp/.X11-unix/X{row['display']}").exists():raise SystemExit(f"preformal display occupied {row['display']}")
    receipt.write_text(json.dumps({'task':schedule['task'],'formal_invocation':1,'reruns':0,'started_unix_ns':time.time_ns()},indent=2,sort_keys=True)+'\n')
    rows=[]; case_hashes={}; errors=[]
    t0=time.monotonic_ns()
    for row in schedule['rows']:
        case_dir=ROOT/'cases'/row['case_id'];case_dir.mkdir(parents=True,exist_ok=False)
        cmd=[sys.executable,str(ROOT/'run_case.py'),'--capacity',str(row['capacity']),'--display',str(row['display']),'--out',str(case_dir)]
        if row['replace']:cmd.append('--replace')
        cp=subprocess.run(cmd,cwd=ROOT,text=True,capture_output=True,timeout=12)
        (case_dir/'stdout.txt').write_text(cp.stdout);(case_dir/'stderr.txt').write_text(cp.stderr)
        if cp.returncode!=0:
            errors.append({'case_id':row['case_id'],'error':'runner_return','returncode':cp.returncode});continue
        rp=case_dir/'result.json'; r=json.loads(rp.read_text()); verr=validate_case(row,r)
        if verr:errors.append({'case_id':row['case_id'],'error':'gate','details':verr})
        rows.append({'case_id':row['case_id'],'capacity':row['capacity'],'replace':row['replace'],'groundings':r['groundings'],'reuses':r['reuses'],'clicks':[x['target'] for x in r['fixture_clicks']],'old_probe_count':len(r['old_probes']),'old_probe_statuses':[x['status'] for x in r['old_probes']],'terminal_button_neutral':r['terminal_button_neutral'],'step_surfaces':[x['surface'] for x in r['steps']]})
        case_hashes[row['case_id']]={'result_sha256':sha(rp),'fixture_sha256':sha(case_dir/'fixture.jsonl')}
    elapsed=time.monotonic_ns()-t0
    cells={}
    for k in (1,2):
        for repl in (False,True):
            key=f"k{k}_{'replace' if repl else 'stable'}"; rs=[x for x in rows if x['capacity']==k and x['replace']==repl]
            cells[key]={'sessions':len(rs),'groundings':[x['groundings'] for x in rs],'reuses':[x['reuses'] for x in rs],'correct_sessions':sum(x['clicks']==['A','B','A','B'] for x in rs),'old_probe_count':sum(x['old_probe_count'] for x in rs)}
    pass_gate=(not errors and len(rows)==20 and all(v['sessions']==5 for v in cells.values()))
    out={'task':schedule['task'],'formal_invocations':1,'reruns':0,'session_count':len(rows),'rows':rows,'cells':cells,'case_hashes':case_hashes,'errors':errors,'elapsed_ns_descriptive':elapsed,'pass':pass_gate,'decision':'PASS_TARGET_HANDLE_CAPACITY_X11_SCOPED' if pass_gate else 'FAIL_TARGET_HANDLE_CAPACITY_X11_FORMAL'}
    resultp.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps({'decision':out['decision'],'sessions':len(rows),'cells':cells,'errors':errors,'elapsed_ns_descriptive':elapsed},sort_keys=True))
    raise SystemExit(0 if pass_gate else 1)
if __name__=='__main__':main()
