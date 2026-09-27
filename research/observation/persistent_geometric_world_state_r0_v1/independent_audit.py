import argparse, json
from pathlib import Path
from runner import execute

if __name__=="__main__":
    ap=argparse.ArgumentParser(); ap.add_argument("result"); ap.add_argument("--out",required=True); a=ap.parse_args()
    r=json.loads(Path(a.result).read_text())
    regenerated=execute(r["metrics"]["traces"])
    keys=("candidate_oracle_mismatch","baseline_false_current","compaction_semantic_changes","fresh_reobservations_current",
          "candidate_false_current","candidate_overinvalidations","aba_stress","compact_stress","occlude_stress","infer_stress")
    diffs={k:[r["metrics"].get(k),regenerated["metrics"].get(k)] for k in keys if r["metrics"].get(k)!=regenerated["metrics"].get(k)}
    out={"pass":not diffs and r["decision"]==regenerated["decision"],"metric_differences":diffs,
         "regenerated_decision":regenerated["decision"]}
    Path(a.out).write_text(json.dumps(out,indent=2,sort_keys=True)+"\n")
    print(json.dumps(out,indent=2,sort_keys=True))
    raise SystemExit(0 if out["pass"] else 5)
