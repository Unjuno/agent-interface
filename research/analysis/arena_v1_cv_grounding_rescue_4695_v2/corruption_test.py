#!/usr/bin/env python3
"""Mutate frozen evidence in memory and require the independent oracle to reject it."""
from __future__ import annotations
import copy,json,sys
from pathlib import Path
from audit import audit

def main():
    if len(sys.argv)!=4: raise SystemExit("usage: corruption_test.py v1-dir v2-dir predictions.json")
    roots=[Path(sys.argv[1]),Path(sys.argv[2])]
    manifests=[json.loads((r/"manifest.json").read_text(encoding="utf-8")) for r in roots]
    baseline=json.loads(Path(sys.argv[3]).read_text(encoding="utf-8"))
    cases={}
    bad=copy.deepcopy(baseline); row=next(r for r in bad["rows"] if r["id"]=="case-02-positive"); row["box_xyxy"]=[0,0,5,5]; cases["wrong_positive_box"]=(manifests,bad)
    bad=copy.deepcopy(baseline); row=next(r for r in bad["rows"] if r["id"]=="case-07-absent"); row.update(status="PROPOSAL",box_xyxy=[10,10,60,60]); cases["guessed_absent"]=(manifests,bad)
    bad=copy.deepcopy(baseline); row=next(r for r in bad["rows"] if r["id"]=="case-10-ambiguous-multiple"); row.update(status="PROPOSAL",box_xyxy=[10,10,60,60]); cases["guessed_ambiguous"]=(manifests,bad)
    bad=copy.deepcopy(baseline); bad["rows"].pop(); cases["dropped_denominator"]=(manifests,bad)
    bad=copy.deepcopy(baseline); bad["rows"][1]["id"]=bad["rows"][0]["id"]; cases["duplicate_identity"]=(manifests,bad)
    altered=copy.deepcopy(manifests); altered[0]["rows"][0]["sha256"]="0"*64; cases["altered_input_binding"]=(altered,copy.deepcopy(baseline))
    results={}
    for name,(ms,pred) in cases.items():
        report=audit(roots,ms,pred)
        results[name]=bool(report["errors"])
    result={"controls":results,"passed":sum(results.values()),"total":len(results)}
    print(json.dumps(result,indent=2))
    raise SystemExit(0 if all(results.values()) else 1)

if __name__=="__main__": main()
