"""Single frozen host construction execution; no verifier backend is called."""
import hashlib
import json
from pathlib import Path

from candidate import preflight

HERE=Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    freeze=json.loads((HERE/"FREEZE.json").read_text())
    for name,digest in freeze["source_sha256"].items():
        if sha(HERE/name)!=digest:
            raise SystemExit(f"frozen source changed: {name}")
    cases=json.loads((HERE/"cases.json").read_text())
    registry=json.loads((HERE/"registry.json").read_text())
    decisions=[preflight(row["ir"],row["assignment"],registry,cases["resources"]) for row in cases["cases"]]
    out=HERE/"results"/"host-construction-01"
    out.mkdir(parents=True,exist_ok=False)
    raw={"schema":"verifier_registry_5273_raw.v2","allocation":freeze["allocation"],
         "base_commit":freeze["base_commit"],"freeze_sha256":sha(HERE/"FREEZE.json"),
         "registry_sha256":sha(HERE/"registry.json"),"cases_sha256":sha(HERE/"cases.json"),
         "parent_ir_candidate_sha256":freeze["parent_ir_candidate_sha256"],"decisions":decisions}
    encoded=json.dumps(raw,sort_keys=True,indent=2)+"\n"
    (out/"RAW.json").write_text(encoded)
    (out/"runner.stdout.txt").write_text(json.dumps({"status":"EXECUTED_HOST_CONSTRUCTION_ONLY","cases":len(decisions)})+"\n")
    (out/"runner.stderr.txt").write_text("")
    print(json.dumps({"status":"EXECUTED_HOST_CONSTRUCTION_ONLY",
                      "raw_sha256":hashlib.sha256(encoded.encode()).hexdigest(),"cases":len(decisions)},sort_keys=True))


if __name__=="__main__":
    main()
