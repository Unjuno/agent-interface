from pathlib import Path
import base64,gzip,hashlib,io,json,shutil,tarfile

HERE=Path(__file__).resolve().parent
OLD_TASK="DECISION-POLICY-CACHE-XTERM-TRANSFER-20260918-001"
NEW_TASK="DECISION-POLICY-CACHE-XTERM-PARENT-ENV-A2-20260918-002"
NEW_BRANCH="research/decision-policy-cache-xterm-parent-env-a2-20260918"

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    m=json.loads((HERE/"PARENT_SOURCE_MANIFEST.json").read_text())
    b64=b"".join((HERE/("PARENT_"+n)).read_bytes() for n in m["parts"])
    raw=base64.b64decode(b64,validate=True)
    assert len(raw)==m["gzip_bytes"]
    assert hashlib.sha256(raw).hexdigest()==m["gzip_sha256"]
    tar=gzip.decompress(raw)
    assert len(tar)==m["tar_bytes"]
    assert hashlib.sha256(tar).hexdigest()==m["tar_sha256"]
    parent=HERE/"reconstructed_parent"; out=HERE/"reconstructed_source"
    for p in (parent,out):
        if p.exists(): shutil.rmtree(p)
        p.mkdir()
    with tarfile.open(fileobj=io.BytesIO(tar),mode="r:") as tf:
        tf.extractall(parent,filter="data")
    for n,want in m["files"].items():
        assert sha(parent/n)==want,(n,sha(parent/n),want)
    shutil.copytree(parent,out,dirs_exist_ok=True)

    r=out/"runner.py"; s=r.read_text()
    assert "D=display.Display(env['DISPLAY'])" in s
    s=s.replace(OLD_TASK,NEW_TASK)
    old="    try:\n        xvfb,env=start_xvfb(cr);title='AI1349-'+case_id\n        xterm=subprocess.Popen"
    new="    parent_display=os.environ.get('DISPLAY');parent_xauthority=os.environ.get('XAUTHORITY');parent_env_scoped=False\n    try:\n        xvfb,env=start_xvfb(cr);title='AI1359-'+case_id\n        os.environ['DISPLAY']=env['DISPLAY'];os.environ['XAUTHORITY']=env['XAUTHORITY'];parent_env_scoped=True\n        xterm=subprocess.Popen"
    assert old in s
    s=s.replace(old,new,1)
    old2="        cleanup['socket_residual']=sockpath.exists()\n"
    new2="        cleanup['socket_residual']=sockpath.exists()\n        if parent_env_scoped:\n            if parent_display is None: os.environ.pop('DISPLAY',None)\n            else: os.environ['DISPLAY']=parent_display\n            if parent_xauthority is None: os.environ.pop('XAUTHORITY',None)\n            else: os.environ['XAUTHORITY']=parent_xauthority\n"
    assert s.count(old2)==1
    s=s.replace(old2,new2,1)
    r.write_text(s)

    for name in ("audit.py","PLAN.md","launcher.py","supervisor.py","common.py","corruption.py"):
        p=out/name
        if p.exists():
            t=p.read_text()
            if OLD_TASK in t: p.write_text(t.replace(OLD_TASK,NEW_TASK))
    sp=out/"schedule.json"
    q=json.loads(sp.read_text());q["task"]=NEW_TASK;q["issue"]=1359;q["branch"]=NEW_BRANCH
    sp.write_text(json.dumps(q,indent=2,sort_keys=True)+"\n")
    hashes={n:sha(out/n) for n in sorted(m["files"])}
    print(json.dumps({"pass":True,"files":hashes},sort_keys=True))

if __name__=="__main__": main()
