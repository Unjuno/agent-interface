"""Post-formal corruption challenge harness for Issue #3830."""
import copy, json, pathlib, subprocess, sys, tempfile
source=pathlib.Path(sys.argv[1]).resolve()
result_dir=pathlib.Path(sys.argv[2]).resolve()
baseline=json.loads((result_dir/"RESULT.json").read_bytes())
cases={
 "altered_report_digest": lambda x: x["cases"]["short_write"].__setitem__("recovered_report_sha256","0"*64),
 "forged_complete_recovery": lambda x: x["cases"]["request_only_crash"].__setitem__("recovery_state","completed"),
 "forged_full_delivery": lambda x: x["cases"]["short_write"].__setitem__("delivery_state","delivered"),
}
out=[]
with tempfile.TemporaryDirectory(prefix="issue3830-corruption-") as td:
 root=pathlib.Path(td)
 for name,mutate in cases.items():
  case=root/name
  case.mkdir()
  candidate=copy.deepcopy(baseline)
  mutate(candidate)
  (case/"RESULT.json").write_text(json.dumps(candidate),encoding="utf-8")
  proc=subprocess.run([sys.executable,str(source/"auditor.py"),str(source),str(case)],capture_output=True,text=True)
  out.append({"case":name,"auditor_returncode":proc.returncode,"auditor_stdout":proc.stdout.strip(),"rejected":proc.returncode!=0})
passed=all(row["rejected"] for row in out)
print(json.dumps({"status":"PASS_CORRUPTION_CONTROLS" if passed else "FAIL_CORRUPTION_CONTROLS","cases":out},sort_keys=True))
sys.exit(0 if passed else 1)
