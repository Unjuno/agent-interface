"""Independent structural audit of the frozen HWND reuse batch receipt."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
conditions = json.loads((ROOT / "conditions.json").read_text(encoding="utf-8"))
raw = json.loads((ROOT / "raw.json").read_text(encoding="utf-8"))
checks = []


def check(name, passed):
    checks.append({"check": name, "passed": bool(passed)})


count = conditions["cohort_size"]
check("attempt_id_matches", raw["attempt_id"] == conditions["attempt_id"])
check("source_commit_matches", raw["source_commit"] == conditions["source_commit"])
check("no_input_or_activation", raw["input_sent"] is False and raw["window_activated"] is False)
check("cohort_sizes_exact", len(raw["first"]) == count and len(raw["second"]) == count)
check("each_cohort_has_unique_handles", len({r["hwnd"] for r in raw["first"]}) == count
      and len({r["hwnd"] for r in raw["second"]}) == count)
check("all_first_handles_destroyed_before_second", len(raw["first_cleanup"]) == count
      and all(r["was_window"] and r["destroy_succeeded"]
              and not r["is_window_after_destroy"] for r in raw["first_cleanup"]))
check("all_second_handles_destroyed", len(raw["second_cleanup"]) == count
      and all(r["was_window"] and r["destroy_succeeded"]
              and not r["is_window_after_destroy"] for r in raw["second_cleanup"]))
check("same_pid_thread_creation_identity", all(
    row["identity"] == raw["first"][0]["identity"]
    for row in raw["first"] + raw["second"]))
matches = raw["same_handle_matches"]
expected = ("COUNTEREXAMPLE_CONFIRMED" if any(m["same_generation"] for m in matches)
            else "REUSED_HANDLE_DISTINGUISHED" if matches
            else "NO_HANDLE_REUSE_OBSERVED_IN_THIS_BATCH")
check("status_matches_frozen_discriminator", raw["status"] == expected)
check("reuse_identity_and_generation_computed_from_raw", all(
    first["identity"] == second["identity"]
    and first["generation"] == second["generation"]
    for match in matches if match["same_generation"]
    for first in [next(r for r in raw["first"] if r["hwnd"] == match["hwnd"])]
    for second in [next(r for r in raw["second"] if r["hwnd"] == match["hwnd"])]))

result = {"schema": "win32-hidden-hwnd-reuse-batch-audit-v1",
          "attempt_id": raw["attempt_id"], "status": raw["status"],
          "checks": checks, "passed": sum(c["passed"] for c in checks),
          "total": len(checks)}
(ROOT / "audit.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
print(json.dumps(result, indent=2))
if result["passed"] != result["total"]:
    raise SystemExit(1)
