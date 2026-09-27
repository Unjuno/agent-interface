#!/usr/bin/env python3
"""Run the byte-identical v1 proposal candidate on both fixed cohorts."""
from __future__ import annotations
import json, sys
from pathlib import Path
from refine import detect

def main():
    if len(sys.argv)!=4: raise SystemExit("usage: run_candidate.py v1-panels v2-panels predictions.json")
    roots=[Path(sys.argv[1]),Path(sys.argv[2])]; rows=[]
    for root in roots:
        panel_root=root/"panels" if (root/"panels").is_dir() else root
        for p in sorted(panel_root.glob("*.png")):
            rows.append({"id":p.stem,**detect(p)})
            if p.stem=="case-01-retained-arena": rows[-1]["source_point_xy"]=[920,640]
    out=Path(sys.argv[3]); out.write_text(json.dumps({"rows":rows},indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"rows":len(rows),"proposals":sum(r["status"]=="PROPOSAL" for r in rows),"abstentions":sum(r["status"]=="ABSTAIN" for r in rows)},indent=2))
if __name__=="__main__": main()
