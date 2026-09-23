import pathlib,subprocess,tempfile,json,sys
base=pathlib.Path(__file__).parent
for arm in ['uid_only','uid_pid']:
  with tempfile.TemporaryDirectory() as td:
    pathlib.Path(td).chmod(0o755); out=pathlib.Path(td)/'c'; cp=subprocess.run([sys.executable,str(base/'run_case.py'),'--arm',arm,'--scenario','B_change','--case-id','construction-'+arm,'--out',str(out)],capture_output=True,text=True)
    assert cp.returncode==0,cp.stderr
    r=json.loads((out/'result.json').read_text()); assert r['broker']['peer_uid']==65534 and r['broker']['peer_gid']==65534 and r['broker']['peer_pid']!=r['broker']['helper_pid']
    if arm=='uid_only': assert r['committed'] and r['broker']['allowed'] and r['task']['b_source']=='scm_rights_fd' and sorted(r['task']['token'])==['A']
    else: assert not r['committed'] and not r['broker']['allowed'] and r['task']['b_source']=='owner_socket' and sorted(r['task']['token'])==['A','B']
print('PASS_STATIC')
