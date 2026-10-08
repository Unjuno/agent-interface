"""Additive post-run reconciliation of A07 cancel events requiring no input release."""
from pathlib import Path
import hashlib
import json

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
ROOT = REPO / "results-local/doom/map01-v39-live-threat-guard-a07-20261009"


def jsonl(path):
    if not path.is_file():
        return []
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def empty_release(row):
    release = row.get("release")
    return (isinstance(release, dict) and release.get("verified") is True and
            release.get("keys_down") == [] and release.get("buttons_down") == [] and
            release.get("keys_unknown") == [])


def main():
    events = jsonl(ROOT / "episode/runtime/events.jsonl")
    scorer = jsonl(ROOT / "episode/runtime/scorer-events.jsonl")
    report = json.loads((ROOT / "episode/report.json").read_text())
    audit = json.loads((ROOT / "AUDIT.json").read_text())
    cancellations = [row for row in events if row.get("event") == "cancel_requested"]
    releases = {row.get("id"): row for row in events if row.get("event") == "input_released"}
    terminals = {row.get("id"): row for row in events if row.get("event") == "terminal"}
    rows = []
    for cancel in cancellations:
        ident = cancel.get("id")
        admitted_downs = [row for row in events if row.get("event") == "input_admission" and
                          row.get("id") == ident]
        transitions = [row for row in events if row.get("event") == "input_release_transition" and
                       row.get("id") == ident]
        terminal = terminals.get(ident)
        release_event = releases.get(ident)
        has_input = bool(admitted_downs)
        per_key_complete = all(row.get("release_batch_complete") is True and
                               row.get("owner_thread_keyup_verified") is True
                               for row in transitions)
        accounted = (bool(transitions) and per_key_complete) if has_input else not transitions
        custody_ok = (cancel.get("matched") is True and terminal is not None and
                      empty_release(terminal) and accounted and
                      ((release_event is not None and empty_release({"release": release_event.get("owner_release")}))
                       if has_input else release_event is None))
        rows.append({"id": ident, "matched": cancel.get("matched"),
                     "input_admitted_before_cancel": len(admitted_downs),
                     "per_key_release_transitions": len(transitions),
                     "input_released_event_present": release_event is not None,
                     "verified_empty_terminal": empty_release(terminal or {}),
                     "custody_ok": custody_ok})
    decisions = report.get("decisions", [])
    guards = [d for d in decisions if isinstance(d.get("policy_invalidation"), dict) and
              (d["policy_invalidation"].get("reason") == "health:below_hard_minimum" or
               d["policy_invalidation"].get("outcomes", {}).get("health", {}).get("reason") == "below_hard_minimum")]
    useful = [e for e in scorer if e.get("useful") is True and
              e.get("kind") in ("KILL_COUNT_INCREASE", "MAP_EXIT")]
    safety_ok = bool(cancellations) and all(row["custody_ok"] for row in rows)
    scope_exposed = bool(guards) and bool(useful)
    status = "PASS" if safety_ok and scope_exposed else ("HOLD" if safety_ok else "FAIL")
    result = {
        "schema": "map01-v39-live-threat-guard-audit-v2",
        "allocation": "map01-v39-live-threat-guard-a07-20261009",
        "status": status,
        "formal_pass": status == "PASS",
        "supersedes": None,
        "preserves_original_audit_sha256": hashlib.sha256((ROOT / "AUDIT.json").read_bytes()).hexdigest(),
        "interpretation": "The original audit required an input_released event for every matched cancellation. Four matched covers had no input_admission or per-key transition, so no per-input release event was due; each still had a verified empty terminal release. The six covers with admitted input all had a matching empty release event and complete per-key custody. Missing hard-guard exposure and useful scorer event therefore yield HOLD, not a release-safety FAIL.",
        "checks": {"all_matched_cancellations_closed_empty": safety_ok,
                   "all_admitted_input_cancel_releases_verified": safety_ok,
                   "hard_health_guard_exposed": bool(guards),
                   "useful_feedback_during_pending_model": bool(useful)},
        "counts": {"matched_cancellations": len(cancellations),
                   "cancellations_with_admitted_input": sum(r["input_admitted_before_cancel"] > 0 for r in rows),
                   "cancellations_without_admitted_input": sum(r["input_admitted_before_cancel"] == 0 for r in rows),
                   "matched_input_release_events": sum(r["input_released_event_present"] for r in rows),
                   "hard_health_guards": len(guards), "useful_scorer_events": len(useful)},
        "per_cancellation": rows,
        "score": json.loads((ROOT / "episode/runtime/score.json").read_text()),
        "scope": "Single current-main MAP01 episode; no threat-control guard exposure, independently useful task effect, or MAP01 exit. X11 receipts are server-side only.",
    }
    (ROOT / "AUDIT_V2.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
    return 0 if status in ("PASS", "HOLD") else 1


if __name__ == "__main__":
    raise SystemExit(main())
