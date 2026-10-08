#!/usr/bin/env python3
"""Freeze A06 source, fixed crop inputs, retained task oracle and host identity."""
import hashlib,json,os,pathlib,platform,subprocess,sys
ROOT=pathlib.Path(__file__).resolve().parents[3]; PKG=pathlib.Path(__file__).resolve().parent
A04="research/analysis/pillow_focused_observation_payload_1998_t0_a04_20261009"; FRAME="chromium-3ef7a4415c4f"
def sha(b): return hashlib.sha256(b).hexdigest()
def main():
 designp=A04+"/design.json"; outp=A04+"/results/candidate.stdout"; design=json.loads((ROOT/designp).read_text()); a04=json.loads((ROOT/outp).read_text()); frame=next(x for x in design["frames"] if x["frame_id"]==FRAME); rows=[r for r in a04["rows"] if r["frame_id"]==FRAME and r["selected_kind"]=="FOCUSED_REGION"]
 if len(rows)!=20: raise SystemExit(f"expected 20 fixed crops, got {len(rows)}")
 run="research/observation_gating/results/baseline-screen-02/chromium-1101-O0"; resultp=run+"/result.json"; submittedp=run+"/submitted.txt"; result=json.loads((ROOT/resultp).read_text()); submitted=(ROOT/submittedp).read_text().strip()
 if result["goal"]["token"]!="t001101" or result["oracle"]["actual"].get("value")!=["t001101"] or submitted!="value=t001101": raise SystemExit("retained Chromium task oracle mismatch")
 tess=pathlib.Path(os.path.realpath("/run/current-system/sw/bin/tesseract")); data=tess.parent.parent/"share/tessdata"; eng=data/"eng.traineddata"; version=subprocess.run([str(tess),"--version"],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,check=True).stdout.decode().splitlines()[0]
 paths={designp,outp,A04+"/FREEZE.json",A04+"/OUTPUT_SHA256SUMS.txt",A04+"/results/audit.stdout",A04+"/REPORT.md",frame["source_png_path"],frame["ledger_path"],resultp,submittedp,"research/observation_gating/gui_suite.py"}
 paths.update(A04+"/"+r["focus_png_path"] for r in rows); inputs={p:sha((ROOT/p).read_bytes()) for p in sorted(paths)}
 code={p:sha((PKG/p).read_bytes()) for p in ("candidate.py","auditor.py","formal_runner.py","freeze_sources.py")}
 base=subprocess.run(["git","-C",str(ROOT),"rev-parse","origin/main"],stdout=subprocess.PIPE,check=True).stdout.decode().strip()
 f={"schema":"a06-freeze-v1","allocation":"LABEL-CONTROL-AMBIGUITY-1998-T0-A06-20261009","base_main_commit":base,"depends_on_a05_head":"673878c504027c23837f12544bd2c025443496ef","frame_id":FRAME,"epoch":7,"first_action_id":"type_token","a04_package":A04,"a04_design_path":designp,"a04_candidate_path":outp,"ledger_path":frame["ledger_path"],"frame_png_path":frame["source_png_path"],"result_json_path":resultp,"submitted_path":submittedp,"marker":"001101","full_payload_bytes":next(x["full_payload_bytes"] for x in a04["rows"] if x["frame_id"]==FRAME),"tesseract_path":str(tess),"tesseract_sha256":sha(tess.read_bytes()),"tesseract_version":version,"tessdata_dir":str(data),"eng_traineddata_path":str(eng),"eng_traineddata_sha256":sha(eng.read_bytes()),"psm":11,"python_executable":os.path.realpath(sys.executable),"python_version":sys.version,"platform":platform.platform(),"machine":platform.machine(),"kernel_release":platform.release(),"candidate_invocations":1,"auditor_invocations":1,"retries":0,"inputs":inputs,"code_sources":code,"scope":"one retained pre-submit Chromium view and exact numeric cue Tesseract extractability only"}
 b=(json.dumps(f,sort_keys=True,indent=2)+"\n").encode(); (PKG/"FREEZE.json").write_bytes(b); (PKG/"FREEZE.sha256").write_text(sha(b)+"  FREEZE.json\n"); print(json.dumps({"freeze_sha256":sha(b),"input_count":len(inputs),"crop_count":len(rows),"code_count":len(code),"base_main_commit":base},sort_keys=True))
if __name__=="__main__": main()
