"""Single-shot runner + independent audit coordinator; preserves typed STOP."""
import argparse
import hashlib
import json
import traceback
from pathlib import Path

import runner
import audit


def write_new(path,data):
    with path.open("xb") as f: f.write(data)


def main():
    p=argparse.ArgumentParser(); p.add_argument("--out",required=True); args=p.parse_args()
    out=Path(args.out)
    if not out.is_dir() or any(out.iterdir()): raise SystemExit("formal output directory must exist and be empty")
    phase="runner"
    try:
        payload=runner.generate_result()
        raw=(json.dumps(payload,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
        write_new(out/"FORMAL_RESULT.json",raw)
        phase="audit"
        result=audit.audit(payload,raw)
        encoded=(json.dumps(result,sort_keys=True,separators=(",",":"),allow_nan=False)+"\n").encode()
        write_new(out/"AUDIT.json",encoded)
        print(json.dumps({"formal":"COMPLETE","audit":result["audit"],"decision":result["decision_recomputed"],
                          "errors":len(result["errors"]),"raw_sha256":hashlib.sha256(raw).hexdigest()},sort_keys=True))
        return 0 if result["audit"]=="PASS" else 2
    except Exception as exc:
        stop={"status":"STOP","phase":phase,"exception":type(exc).__name__,"message":str(exc),
              "traceback":traceback.format_exc(),"no_retry":True}
        write_new(out/"STOP.json",(json.dumps(stop,sort_keys=True,separators=(",",":"))+"\n").encode())
        print(json.dumps({"formal":"STOP","phase":phase,"exception":type(exc).__name__,"no_retry":True},sort_keys=True))
        return 1


if __name__=="__main__": raise SystemExit(main())
