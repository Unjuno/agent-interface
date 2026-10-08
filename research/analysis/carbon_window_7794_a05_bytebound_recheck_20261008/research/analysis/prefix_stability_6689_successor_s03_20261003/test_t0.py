import subprocess,sys,tempfile
fixture=sys.argv[1]; candidate=sys.argv[2]; auditor=sys.argv[3]
with tempfile.TemporaryDirectory() as d:
    out=d+"/candidate.json"
    with open(out,"w") as f: subprocess.run([sys.executable,candidate,fixture],check=True,stdout=f)
    result=subprocess.run([sys.executable,auditor,fixture,out],check=True,capture_output=True,text=True)
    print(result.stdout.strip())
