from pathlib import Path
import json, os, subprocess, sys, time
repo=Path(__file__).resolve().parents[3]
out=Path(__file__).resolve().parent
modules=['research.live_control.test_adaptive_acquisition_compiled_gui_v1', 'research.live_control.test_adaptive_acquisition_caller_v3', 'runtime.core_v1.test_compiled_admission_custody_01a0ff35', 'runtime.core_v1.test_compiled_admission_sequence_01a0ff33', 'runtime.core_v1.test_compiled_callback_custody_01a0ff35', 'runtime.core_v1.test_compiled_callback_failure_composition', 'runtime.core_v1.test_compiled_clock_custody', 'runtime.core_v1.test_compiled_custody_effect_join_01a0ff35', 'runtime.core_v1.test_compiled_effect_evidence_01a0ff32', 'runtime.core_v1.test_compiled_effect_return_custody_01a0ff35', 'runtime.core_v1.test_compiled_gui', 'runtime.core_v1.test_compiled_gui_effect_verifier_exception', 'runtime.core_v1.test_compiled_gui_journal_exception', 'runtime.core_v1.test_compiled_invalid_delivery_reconciliation', 'runtime.core_v1.test_compiled_literal_unknown_01a0ff35', 'runtime.core_v1.test_compiled_observation_order', 'runtime.core_v1.test_compiled_release_recovery_01a0ff35', 'runtime.core_v1.test_compiled_terminal_return_custody_01a0ff35', 'runtime.core_v1.test_compiled_unverified_release_reconciliation']
env=os.environ.copy()
env["PYTHONPATH"]=os.pathsep.join([str(repo), str(repo/"research/live_control")])
runs=[]
for index,target in enumerate(modules,1):
 command=[sys.executable]
 if "-O" in sys.argv: command.append("-O")
 command += ["-m","unittest",target,"-v"]
 started=time.time()
 proc=subprocess.run(command,cwd=repo,env=env,capture_output=True)
 stem=f"{index:02d}-{target.rsplit('.',1)[-1]}"+("-optimized" if "-O" in sys.argv else "-normal")
 (out/(stem+".stdout.bin")).write_bytes(proc.stdout)
 (out/(stem+".stderr.bin")).write_bytes(proc.stderr)
 (out/(stem+".exitcode.txt")).write_text(str(proc.returncode)+"\n")
 runs.append({"name":stem,"module":target,"command":command,"exit_code":proc.returncode,"duration_s":round(time.time()-started,3),"stdout":proc.stdout.decode("utf-8","replace"),"stderr":proc.stderr.decode("utf-8","replace")})
name="optimized_runs.json" if "-O" in sys.argv else "normal_runs.json"
(out/name).write_text(json.dumps(runs,indent=2)+"\n")
print(json.dumps([{"module":r["module"],"exit_code":r["exit_code"],"duration_s":r["duration_s"]} for r in runs],indent=2))
sys.exit(0 if all(r["exit_code"]==0 for r in runs) else 1)
