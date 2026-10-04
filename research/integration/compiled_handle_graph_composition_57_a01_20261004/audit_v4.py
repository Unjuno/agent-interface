"""Read-only successor audit with corrected repository-root resolution."""
import json
import subprocess
import sys
from pathlib import Path

from audit_v2 import audit as audit_v2

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MODULES = {
    "compiled_gui.py": "runtime/core_v1/compiled_gui.py",
    "handles.py": "runtime/guarded_x11_v1/handles.py",
    "handles_base.py": "runtime/guarded_x11_v1/handles_base.py",
    "handles_texture.py": "runtime/guarded_x11_v1/handles_texture.py",
}


def _blob(revision, path):
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "rev-parse", f"{revision}:{path}"],
        text=True).strip()


def audit(candidate):
    freeze = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))
    behavior = audit_v2(candidate)
    base = freeze["integration_base"]
    pinned = freeze["source_module_git_blobs"]
    base_blobs = {name: _blob(base, path) for name, path in MODULES.items()}
    if base_blobs != pinned:
        raise ValueError("frozen base module blobs do not match freeze")
    raw_label = candidate.get("source_main")
    label_matches = raw_label == base
    raw_label_blobs = ({name: _blob(raw_label, path) for name, path in MODULES.items()}
                       if isinstance(raw_label, str) and len(raw_label) == len(base) else {})
    return {
        "schema": "compiled-handle-graph-composition-audit-v4",
        "verdict": behavior["verdict"] if label_matches else "FAIL_SOURCE_BASE_LABEL_MISMATCH",
        "reason": ("candidate source_main matches frozen integration base" if label_matches else
                   "candidate source_main differs from FREEZE integration_base; frozen decision classifies any mismatch as FAIL"),
        "candidate_source_main_label": raw_label,
        "frozen_integration_base": base,
        "source_module_blobs_at_frozen_base": base_blobs,
        "source_module_blobs_at_raw_label": raw_label_blobs,
        "module_identity_matches_both": base_blobs == pinned and raw_label_blobs == pinned,
        "behavioral_counts_from_read_only_v2_audit": behavior["counts"],
        "behavioral_audit_v2_passed": behavior["verdict"] == "PASS",
        "execution_repeated": False,
        "scope": "retained offline test-double records only; source-label failure is preserved, not repaired by rewriting raw output",
    }


if __name__ == "__main__":
    candidate = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    print(json.dumps(audit(candidate), indent=2, sort_keys=True))
