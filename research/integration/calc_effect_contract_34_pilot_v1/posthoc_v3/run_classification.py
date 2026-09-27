"""CLI to reproduce the retained post-hoc classification in a fresh output path."""
from __future__ import annotations

import argparse
import json
import pathlib

from classify import classify


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument("--raw",type=pathlib.Path,required=True)
    parser.add_argument("--audit",type=pathlib.Path,required=True)
    parser.add_argument("--out",type=pathlib.Path,required=True)
    args=parser.parse_args()
    if args.out.exists(): raise FileExistsError(f"refusing to overwrite {args.out}")
    result=classify(json.loads(args.raw.read_text(encoding="utf-8")),json.loads(args.audit.read_text(encoding="utf-8")))
    args.out.parent.mkdir(parents=True,exist_ok=True)
    args.out.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,sort_keys=True))
    return 0


if __name__=="__main__": raise SystemExit(main())
