"""Independent, read-only audit of geometry-review construction03."""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
result = json.loads((root / "construction03/result.json").read_text(encoding="utf-8"))
trace = result.get("trace", {})
errors = []

def raw(key):
    return trace.get(key, {}).get("receipt", {}).get("source", {}).get("raw_report", {}).get("result", {})

before = trace.get("geometry_before", {})
after = trace.get("geometry_after", {})
inspect = trace.get("inspect", {})
review = trace.get("review", {})
stale = raw("stale_dispatch")
fresh = raw("fresh_dispatch")
release = fresh.get("execution", {}).get("releases", [])
calls = [row.get("operation") for row in trace.get("calls", [])]

if not (before.get("WIDTH") == 1600 and before.get("HEIGHT") == 981): errors.append("unexpected initial geometry")
if not (after.get("WIDTH") == 1280 and after.get("HEIGHT") == 760 and (before != after)): errors.append("independent geometry transition missing")
if inspect.get("status") != "needs_review" or inspect.get("evidence", {}).get("window_id") != trace.get("main_window_id"): errors.append("inspect did not bind original root")
if review.get("status") != "target_reviewed" or review.get("window_id") != trace.get("main_window_id") or review.get("binding_revision") != 2: errors.append("review did not advance the same-root binding")
if stale.get("error") != "STALE_BINDING" or stale.get("backend_emissions") != 0 or stale.get("status") != "refused": errors.append("old revision not refused at core with zero emissions")
execution = fresh.get("execution", {})
if fresh.get("status") != "completed" or execution.get("program_emissions") != 2: errors.append("fresh neutral program not completed")
if not release or not all(r.get("verified") and r.get("keys_down") == [] and r.get("buttons_down") == [] for r in release): errors.append("fresh dispatch release not verified neutral")
if trace.get("close", {}).get("status") != "closed" or not trace.get("close", {}).get("release_attempted"): errors.append("session close/release evidence missing")
if trace.get("decision") != "HOLD_INCOMPLETE": errors.append("runner trace decision not preserved as HOLD_INCOMPLETE")
if result.get("decision") != "PASS_GEOMETRY_REVIEW_STALE_BINDING_SCOPED": errors.append("runner top-level decision changed from raw result")
if calls != ["observe", "observe", "inspect_target", "review_target", "dispatch", "dispatch", "close"]: errors.append("unexpected MCP call sequence")

print(json.dumps({
    "schema": "agent-interface/2907-geometry-review-audit-v4",
    "decision": "HOLD_RUNNER_DECISION_INCONSISTENT" if errors else "HOLD_FORMAL_ALLOCATION_AND_EFFECT_ORACLE",
    "errors": errors,
    "scoped_mechanism": "PASS" if not errors else "UNVERIFIED",
    "formal_allocation": False,
    "runner_decisions": {"top_level": result.get("decision"), "trace": trace.get("decision")},
    "geometry": {"before": before, "after": after, "changed": before != after},
    "identity": {"main_window_id": trace.get("main_window_id"), "inspect_window_id": inspect.get("evidence", {}).get("window_id"), "review_window_id": review.get("window_id"), "revision": review.get("binding_revision")},
    "stale_control": stale,
    "fresh_control": {"status": fresh.get("status"), "program_emissions": execution.get("program_emissions"), "releases": release},
    "close": {"status": trace.get("close", {}).get("status"), "release_attempted": trace.get("close", {}).get("release_attempted"), "release_verified": trace.get("close", {}).get("release", {}).get("verified")},
    "scope": "single Calc root geometry/review stale-binding construction only; no independent application-effect oracle; not the mixed-app #2907 acceptance",
}, sort_keys=True, indent=2))
raise SystemExit(2 if errors else 0)
