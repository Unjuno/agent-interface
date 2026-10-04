from pathlib import Path
import subprocess,sys,json
rows=[]
for name in ['test_session_map01_v15', 'test_independent_progress_clock_v2', 'test_main_thread_scorer_polling_v1', 'test_map01_scorer_stdio_adapter_v1', 'test_acknowledged_scorer_v1']:
 p=subprocess.run([sys.executable,"-B","-m","unittest",name,"-v"],capture_output=True)
 Path("/out/"+name+".stdout").write_bytes(p.stdout);Path("/out/"+name+".stderr").write_bytes(p.stderr);rows.append({"module":name,"exit_code":p.returncode})
Path("/out/RESULT.json").write_text(json.dumps(rows,indent=2));print(json.dumps(rows));sys.exit(int(any(r["exit_code"] for r in rows)))
