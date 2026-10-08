import pathlib,subprocess,tempfile,json,sys
base=pathlib.Path(__file__).parent
for arm in ['no_fd','leaked_fd']:
  with tempfile.TemporaryDirectory() as td:
    pathlib.Path(td).chmod(0o755)
    out=pathlib.Path(td)/'c'; cp=subprocess.run([sys.executable,str(base/'run_case.py'),'--arm',arm,'--scenario','B_change','--case-id','construction-'+arm,'--out',str(out)],capture_output=True,text=True)
    assert cp.returncode==0,cp.stderr
    r=json.loads((out/'result.json').read_text())
    if arm=='no_fd': assert not r['committed'] and sorted(r['task']['token'])==['A','B']
    else: assert r['committed'] and sorted(r['task']['token'])==['A'] and r['task']['b_source']=='fd_deserialize'
print('PASS_STATIC')
