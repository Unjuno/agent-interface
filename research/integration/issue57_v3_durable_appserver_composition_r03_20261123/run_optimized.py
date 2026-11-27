from pathlib import Path
import json, os, subprocess, sys, time
repo=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
focused="research.live_control.test_grounding_appserver_usage_transport.GroundingAppServerUsageTransportTest.test_jsonl_provider_success_joins_durable_prospective_custody"
module="research.live_control.test_grounding_appserver_usage_transport"
runs=[]
env=os.environ.copy()
env["PYTHONPATH"]=str(repo)
for name,target in [("focused-optimized",focused),("module-optimized",module)]:
    started=time.time()
    command=[sys.executable,"-O","-m","unittest",target,"-v"]
    proc=subprocess.run(command,cwd=repo,env=env,capture_output=True)
    (out/(name+".stdout.bin")).write_bytes(proc.stdout)
    (out/(name+".stderr.bin")).write_bytes(proc.stderr)
    (out/(name+".exitcode.txt")).write_text(str(proc.returncode)+"\\n")
    runs.append({"name":name,"command":command,"exit_code":proc.returncode,"duration_s":round(time.time()-started,3),"stdout":proc.stdout.decode("utf-8","replace"),"stderr":proc.stderr.decode("utf-8","replace")})
(out/"optimized_runs.json").write_text(json.dumps(runs,indent=2)+"\\n")
print(json.dumps(runs,indent=2))
