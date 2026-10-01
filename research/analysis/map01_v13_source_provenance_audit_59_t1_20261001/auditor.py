"""Independent raw-only source-closure audit; does not import candidate.py."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def git_object(root: Path, commit: str, path: str) -> bytes | None:
    p = subprocess.run(["git", "-C", str(root), "show", f"{commit}:{path}"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p.stdout if p.returncode == 0 else None


def load_expected(prereg: dict) -> dict[str, set[str]]:
    all_pins: dict[str, set[str]] = {}
    for name in ("source_sha256", "canonical_upstream_sha256"):
        part = prereg.get(name)
        if not isinstance(part, dict) or not part:
            raise ValueError(f"missing hash map {name}")
        for path, digest in part.items():
            if not isinstance(path, str) or not path or not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
                raise ValueError(f"invalid hash record {name}:{path}")
            all_pins.setdefault(path, set()).add(digest)
    return all_pins


def verify(root: Path, fixture: dict, raw: dict) -> dict:
    commit, prereg_path = fixture["source_commit"], fixture["prereg_path"]
    prereg_bytes = git_object(root, commit, prereg_path)
    if prereg_bytes is None:
        return {"schema":"map01-current-main-source-closure-audit-v2","disposition":"FAIL_AUDIT_INTEGRITY","errors":["frozen-preregistration-missing"],"error_count":1}
    try:
        pins = load_expected(json.loads(prereg_bytes))
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        return {"schema":"map01-current-main-source-closure-audit-v2","disposition":"FAIL_AUDIT_INTEGRITY","errors":[f"invalid-preregistration:{type(exc).__name__}"],"error_count":1}
    errors=[]
    rows=raw.get("rows") if isinstance(raw,dict) else None
    rows=rows if isinstance(rows,list) else []
    expected_paths=sorted(pins)
    actual_paths=[r.get("path") if isinstance(r,dict) else None for r in rows]
    if actual_paths != expected_paths or len(actual_paths)!=len(set(actual_paths)):
        errors.append("candidate-path-set-mismatch")
    if raw.get("source_commit")!=commit or raw.get("prereg_path")!=prereg_path:
        errors.append("candidate-frozen-identity-mismatch")
    drift=[]
    independent=[]
    for path in expected_paths:
        data=git_object(root,commit,path)
        digest=hashlib.sha256(data).hexdigest() if data is not None else None
        pinlist=sorted(pins[path])
        row=next((r for r in rows if isinstance(r,dict) and r.get("path")==path),None)
        if data is None or len(pinlist)!=1 or digest!=pinlist[0]:
            drift.append(path)
        if row is None or row.get("actual_sha256")!=digest or row.get("expected_sha256")!=pinlist or row.get("present") is not (data is not None):
            errors.append("candidate-row-disagrees-with-independent-read:"+path)
        independent.append({"path":path,"sha256":digest,"matches_pin":data is not None and len(pinlist)==1 and digest==pinlist[0]})
    if raw.get("expected_source_path_count")!=len(expected_paths):
        errors.append("candidate-source-count-mismatch")
    result="FAIL_AUDIT_INTEGRITY" if errors else ("FAIL_PINNED_SOURCE_DRIFT" if drift else "PASS_SOURCE_CLOSURE_ONLY")
    return {"schema":"map01-current-main-source-closure-audit-v2","source_commit":commit,"prereg_path":prereg_path,
            "expected_source_path_count":len(expected_paths),"independently_verified_path_count":len(independent),
            "drift_paths":drift,"errors":errors,"error_count":len(errors),
            "historical_allocation_id":fixture["historical_allocation_id"],"live_validation_authorized":False,
            "disposition":result}


def main() -> None:
    parser=argparse.ArgumentParser()
    parser.add_argument("--repo-root",type=Path,default=ROOT)
    parser.add_argument("--fixture",type=Path,default=Path(__file__).with_name("fixture.json"))
    parser.add_argument("--candidate",type=Path,default=Path(__file__).with_name("candidate_output.json"))
    parser.add_argument("--out",type=Path,required=True)
    args=parser.parse_args()
    fixture=json.loads(args.fixture.read_text(encoding="utf-8"))
    raw=json.loads(args.candidate.read_text(encoding="utf-8"))
    result=verify(args.repo_root,fixture,raw)
    text=json.dumps(result,sort_keys=True,separators=(",",":"))+"\n"
    args.out.write_text(text,encoding="utf-8",newline="\n")
    print(text,end="")
    raise SystemExit(0 if result["error_count"]==0 and result["disposition"]=="PASS_SOURCE_CLOSURE_ONLY" else 1)


if __name__=="__main__":
    main()
