import pathlib,subprocess,tempfile,json,sys
base=pathlib.Path(__file__).parent
for arm in ['control','inject_fd']:
  with tempfile.TemporaryDirectory() as td:
    pathlib.Path(td).chmod(0o755); out=pathlib.Path(td)/'c'; cp=subprocess.run([sys.executable,str(base/'run_case.py'),'--arm',arm,'--scenario','B_change','--case-id','construction-'+arm,'--out',str(out)],capture_output=True,text=True)
    assert cp.returncode==0,cp.stderr
    r=json.loads((out/'result.json').read_text())
    if arm=='control': assert not r['committed'] and sorted(r['task']['token'])==['A','B'] and r['task']['b_source']=='owner_socket'
    else: assert r['committed'] and sorted(r['task']['token'])==['A'] and r['task']['b_source']=='scm_rights_fd'
    assert not any(str(v).endswith('/state.db') for v in r['task']['startup_fd_targets'].values())
print('PASS_STATIC')
