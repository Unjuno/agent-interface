"""Independent, read-only audit for V39 active-frame integrity A02."""
from __future__ import annotations
import hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parent
EXPECTED={"planner-adapter":12,"app-server-client":4,"v39-paired-signal":21,"v39-controller":5,"v39-wait":10,"v39-pair-dispatch":1}
SOURCES={
    'research/doom/map01_overlap_controller_v39.py': '6b3fbf2fe651557a3178a33cbf1ba0145ba5145a54c57b1c8db42252957f4d8f',
    'research/doom/test_map01_overlap_controller_v39_dual_signal.py': 'be74c4e9fbf2aae4254bc94ff6bad9fda67270bf9656874a61f017d780d35a17',
    'research/doom/test_overlap_controller_v39_wait.py': '10b6c377ab97d9d2ccae36d92f86acda61d5c6840286975caf80e3911fa377be'
}
def require(ok,msg):
    if not ok: raise SystemExit("FAIL: "+msg)
def verify_package_hashes():
    manifest=ROOT/"SHA256SUMS"
    require(manifest.is_file(),"SHA256SUMS missing")
    rows=manifest.read_text(encoding="ascii").splitlines()
    require(rows,"SHA256SUMS is empty")
    for row in rows:
        expected,relative=row.split("  ",1)
        path=ROOT/relative
        require(path.is_file(),f"manifest file missing: {relative}")
        actual=hashlib.sha256(path.read_bytes()).hexdigest()
        require(actual==expected,f"manifest hash mismatch: {relative}")
def audit():
    verify_package_hashes()
    report=json.loads((ROOT/"results"/"audit.json").read_text(encoding="utf-8"))
    total=0
    for name,count in EXPECTED.items():
        log=(ROOT/"results"/f"{name}.txt").read_text(encoding="utf-8")
        code=(ROOT/"results"/f"{name}.txt.exit").read_text(encoding="ascii").strip()
        match=re.search(r"Ran (\d+) tests? in ",log)
        require(code=="0",f"{name}: nonzero exit")
        require(match and int(match.group(1))==count,f"{name}: count mismatch")
        require(log.rstrip().endswith("OK"),f"{name}: missing unittest OK")
        total+=count
    require((ROOT/"results"/"py-compile.txt.exit").read_text(encoding="ascii").strip()=="0","py_compile failed")
    require(report.get("total_tests")==total and report.get("test_counts")==EXPECTED,"report counts mismatch")
    for rel,expected in SOURCES.items():
        actual=hashlib.sha256((ROOT.parents[2]/rel).read_bytes()).hexdigest()
        require(actual==expected,f"source hash mismatch: {rel}")
    require(report.get("source_sha256")==SOURCES,"report source mismatch")
    return {"status":"PASS_A02_INDEPENDENT_AUDIT","tested_commit":report.get("tested_commit"),"test_counts":EXPECTED,"total_tests":total,"py_compile":"PASS","sources":"PASS","package_hashes":"PASS"}
if __name__=="__main__": print(json.dumps(audit(),indent=2))
