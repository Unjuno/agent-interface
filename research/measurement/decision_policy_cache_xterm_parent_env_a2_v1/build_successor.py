from pathlib import Path
import hashlib,json,shutil,subprocess

HERE=Path(__file__).resolve().parent
OLD="DECISION-POLICY-CACHE-XTERM-TRANSFER-20260918-001"
NEW="DECISION-POLICY-CACHE-XTERM-PARENT-ENV-A2-20260918-002"
EXPECTED_SHA256="ece381e75321fbac6141caecbead0ae8feeb125a45367038c8d25aab5bf19a6f"

p=HERE/"PARENT_runner.py"; out=HERE/"runner.py"
s=p.read_text()
s=s.replace("TASK='"+OLD+"'","TASK='"+NEW+"'",1)
old="    try:\n        xvfb,env=start_xvfb(cr);title='AI1349-'+case_id\n        xterm=subprocess.Popen"
new="    parent_display=os.environ.get('DISPLAY');parent_xauthority=os.environ.get('XAUTHORITY');parent_env_scoped=False\n    try:\n        xvfb,env=start_xvfb(cr);title='AI1359-'+case_id\n        os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY'];parent_env_scoped=True\n        xterm=subprocess.Popen"
assert old in s
s=s.replace(old,new,1)
old2="        cleanup['socket_residual']=sockpath.exists()\n"
new2="        cleanup['socket_residual']=sockpath.exists()\n        if parent_env_scoped:\n            if parent_display is None: os.environ.pop('DISPLAY',None)\n            else: os.environ['DISPLAY']=parent_display\n            if parent_xauthority is None: os.environ.pop('XAUTHORITY',None)\n            else: os.environ['XAUTHORITY']=parent_xauthority\n"
assert s.count(old2)==1
s=s.replace(old2,new2,1)
out.write_text(s)
assert hashlib.sha256(out.read_bytes()).hexdigest()==EXPECTED_SHA256
print(json.dumps({"pass":True,"runner_sha256":EXPECTED_SHA256},sort_keys=True))
