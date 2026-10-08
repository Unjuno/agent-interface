"""One-shot candidate invocation; exact finite models only."""
from __future__ import annotations
import argparse, hashlib, json
from pathlib import Path
import candidate

ROOT=Path(__file__).resolve().parent


def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--output",default=str(ROOT/"results/first-outcome")); args=ap.parse_args()
    out=Path(args.output)
    if out.exists() and any(out.iterdir()): raise SystemExit("refusing nonempty output: formal run is one-shot")
    out.mkdir(parents=True,exist_ok=True)
    fixtures=json.loads((ROOT/"fixtures.json").read_text())
    result=candidate.evaluate(fixtures)
    target=out/"candidate.json"
    target.write_text(json.dumps(result,indent=2,sort_keys=True)+"\n")
    print(json.dumps({"allocation":fixtures["allocation"],"candidate_invocation":1,"cases":len(result["cases"]),"horizons":len(fixtures["horizons"]),"output":str(target),"output_sha256":hashlib.sha256(target.read_bytes()).hexdigest()},sort_keys=True))

if __name__=="__main__": main()
