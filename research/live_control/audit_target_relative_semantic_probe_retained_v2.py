"""Audit the retained translated-success and resize-refusal result."""
import hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE/"results/target-relative-semantic-probe-live-02"
def read(path):return json.loads(Path(path).read_text(encoding="utf-8"))
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
    receipt=read(ROOT/"retention.json");report=read(ROOT/"report.json")
    checks={"manifest":all((ROOT/name).is_file() and sha(ROOT/name)==digest
                           for name,digest in receipt["manifest"].items()),
        "first_pass":receipt["formal_passed"] is True and receipt["audit_passed"] is True,
        "translation":report["checks"]["fresh_moved_binding"] is True and
                      report["checks"]["relative_translated_success"] is True,
        "fixed_control":report["checks"]["fixed_control_rejects_moved_crop"] is True,
        "resize_refusal":report["checks"]["resize_refuses_before_crop"] is True,
        "evidence_release":report["checks"]["exact_reconciliation"] is True and
                           report["checks"]["independent_saved_value"] is True and
                           report["checks"]["empty_release"] is True,
        "early":report["metrics_ms"]["useful_probe_to_image_ready_ms"]>0 and
                report["metrics_ms"]["useful_client_to_terminal_ms"]>0,
        "no_retry_model":receipt["retry_count"]==report["retry_count"]==0 and
                         report["model_calls"]==0}
    result={"passed":all(checks.values()),"checks":checks,"metrics_ms":report["metrics_ms"],
            "files":receipt["files"],"bytes":receipt["bytes"],"limits":receipt["limits"]}
    (ROOT/"retained-audit.json").write_text(json.dumps(result,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(result,indent=2));return 0 if result["passed"] else 1
if __name__=="__main__":raise SystemExit(main())
