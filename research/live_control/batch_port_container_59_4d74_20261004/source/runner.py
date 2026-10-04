import subprocess,json,sys
from pathlib import Path
rows=[]
for name in ['test_input_owner_v12_batch_release_telemetry', 'test_input_owner_v12_explicit_up_cancel', 'test_executor_v13', 'test_executor_owner_cancel_cause_v1', 'test_executor_release_publication_order_v1', 'test_input_transition_owner_v4']:
 p=subprocess.run([sys.executable,"-B","-m","unittest",name,"-v"],capture_output=True)
 Path("/out/"+name+".stdout").write_bytes(p.stdout);Path("/out/"+name+".stderr").write_bytes(p.stderr);rows.append({"module":name,"exit_code":p.returncode})
Path("/out/RESULT.json").write_text(json.dumps(rows,indent=2));print(json.dumps(rows));sys.exit(int(any(r["exit_code"] for r in rows)))
