"""Audit the retained pre-input target-relative failure."""
import hashlib,json
from pathlib import Path

HERE=Path(__file__).resolve().parent; ROOT=HERE/"results/target-relative-semantic-probe-live-01"
def read(path): return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    retention=read(ROOT/"retention.json"); failure=read(ROOT/"failure.json")
    checks={"manifest":all((ROOT/name).is_file() and sha(ROOT/name)==digest
                           for name,digest in retention["manifest"].items()),
        "failure_preserved":retention["formal_passed"] is False and
                            failure["formal_passed"] is False,
        "all_diagnostics":all(failure["checks"].values()),
        "before_input":failure["terminal"]["steps_completed"]==0 and
                       failure["checks"]["no_submission"] is True and
                       failure["checks"]["no_semantic_probe"] is True,
        "empty_release":failure["checks"]["empty_release"] is True,
        "no_retry":retention["retry_count"]==failure["retry_count"]==0}
    result={"passed":all(checks.values()),"checks":checks,"files":retention["files"],
            "bytes":retention["bytes"],"failure_class":retention["failure_class"]}
    (ROOT/"retained-audit.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2)); return 0 if result["passed"] else 1


if __name__=="__main__": raise SystemExit(main())
