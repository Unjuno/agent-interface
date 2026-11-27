from pathlib import Path
import json,os,subprocess,sys,time
repo=Path(__file__).resolve().parents[3]; out=Path(__file__).resolve().parent
focused="research.live_control.test_grounding_appserver_usage_transport.GroundingAppServerUsageTransportTest.test_jsonl_interrupted_turn_with_observed_usage_reaches_durable_custody"
module="research.live_control.test_grounding_appserver_usage_transport"
env=os.environ.copy(); env["PYTHONPATH"]=str(repo); runs=[]
for name,target in [("focused-optimized",focused),("module-optimized",module)]:
 command=[sys.executable,"-O","-m","unittest",target,"-v"]; started=time.time()
 p=subprocess.run(command,cwd=repo,env=env,capture_output=True)
 (out/(name+".stdout.bin")).write_bytes(p.stdout); (out/(name+".stderr.bin")).write_bytes(p.stderr)
 (out/(name+".exitcode.txt")).write_text(str(p.returncode)+"\n")
 runs.append({"name":name,"command":command,"exit_code":p.returncode,"duration_s":round(time.time()-started,3),"stdout":p.stdout.decode("utf-8","replace"),"stderr":p.stderr.decode("utf-8","replace")})
(out/"optimized_runs.json").write_text(json.dumps(runs,indent=2)+"\n")
print(json.dumps(runs,indent=2))
