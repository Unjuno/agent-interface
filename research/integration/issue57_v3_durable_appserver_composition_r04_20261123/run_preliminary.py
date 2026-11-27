from pathlib import Path
import json,os,subprocess,sys
repo=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
target="research.live_control.test_grounding_appserver_usage_transport.GroundingAppServerUsageTransportTest.test_jsonl_failed_turn_without_usage_stays_unknown_in_prospective_custody"
env=os.environ.copy()
env["PYTHONPATH"]=str(repo)
command=[sys.executable,"-m","unittest",target,"-v"]
proc=subprocess.run(command,cwd=repo,env=env,capture_output=True)
(out/"preliminary_assertion_mismatch.stdout.bin").write_bytes(proc.stdout)
(out/"preliminary_assertion_mismatch.stderr.bin").write_bytes(proc.stderr)
(out/"preliminary_assertion_mismatch.exitcode.txt").write_text(str(proc.returncode)+"\\n")
(out/"preliminary_assertion_mismatch.json").write_text(json.dumps({"command":command,"exit_code":proc.returncode,"stdout":proc.stdout.decode("utf-8","replace"),"stderr":proc.stderr.decode("utf-8","replace")},indent=2)+"\\n")
print(json.dumps({"exit_code":proc.returncode,"stderr":proc.stderr.decode("utf-8","replace")}))
