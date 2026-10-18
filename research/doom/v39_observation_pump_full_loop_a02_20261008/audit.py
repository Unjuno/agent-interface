"""Independent source-identity and full-loop event auditor."""
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
FREEZE = json.loads((HERE / "FREEZE.json").read_text(encoding="utf-8"))


def repo_root():
    for parent in HERE.parents:
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("repository root not found")


def verify_sources(repo=None):
    repo = Path(repo) if repo is not None else repo_root()
    for name, spec in FREEZE["sources"].items():
        data = subprocess.check_output(
            ["git", "-C", str(repo), "show",
             f"{FREEZE['main_commit']}:{spec['path']}"])
        blob = subprocess.check_output(
            ["git", "-C", str(repo), "rev-parse",
             f"{FREEZE['main_commit']}:{spec['path']}"], text=True).strip()
        if blob != spec["git_blob"] or hashlib.sha256(data).hexdigest() != spec["sha256"]:
            raise ValueError(f"frozen source identity mismatch: {name}")


def validate(result, raw_events, freeze=None, repo=None):
    freeze = FREEZE if freeze is None else freeze
    verify_sources(repo)
    if (not isinstance(result, dict) or
            result.get("schema") != "issue59-v39-observation-pump-full-loop-result-a02" or
            result.get("status") != "CONSTRUCTION_OBSERVATION" or
            result.get("main_commit") != freeze["main_commit"]):
        raise ValueError("result identity mismatch")
    cases = result.get("cases")
    if not isinstance(cases, list) or [c.get("case") for c in cases] != [
            "healthy_completion", "invalidation"]:
        raise ValueError("case set mismatch")
    flattened = [{"case": c["case"], **row}
                 for c in cases for row in c["events"]]
    if flattened != raw_events:
        raise ValueError("raw event stream mismatch")
    healthy, invalid = cases
    he = healthy["events"]
    kinds = [row["event"] for row in he]
    delivered = [row for row in he if row["event"] == "monitor_received"]
    terminals = [row for row in he if row["event"] == "terminal_dequeued"]
    renewals = [row for row in he if row["event"] == "cover_renewed"]
    polls = [row for row in he if row["event"] == "planner_future_poll"]
    if (len(delivered) != 3 or any(row["future_pending"] is not True for row in delivered) or
            [row["sequence"] for row in delivered] != [2, 3, 4]):
        raise ValueError("healthy observation delivery mismatch")
    completion_index = max((i for i, row in enumerate(he)
                            if row["event"] == "planner_future_poll" and
                            row.get("done") is True), default=-1)
    if (completion_index < 0 or
            any(row["event"] == "cover_renewed"
                for row in he[completion_index + 1:])):
        raise ValueError("planner completion did not bound renewal")
    if (len(terminals) != 2 or [row["id"] for row in terminals] != ["cover-0", "cover-1"] or
            len(renewals) != 1 or healthy["submitted"] != ["cover-0-renew-0"]):
        raise ValueError("healthy renewal lifecycle mismatch")
    ie = invalid["events"]
    ikinds = [row["event"] for row in ie]
    ihard = next((i for i, row in enumerate(ie)
                  if row["event"] == "monitor_invalidated"), None)
    icancel = next((i for i, row in enumerate(ie)
                    if row["event"] == "executor_cancel_write"), None)
    iinterrupt = next((i for i, row in enumerate(ie)
                       if row["event"] == "planner_interrupt_transport"), None)
    iterminal = next((i for i, row in enumerate(ie)
                      if row["event"] == "terminal_dequeued"), None)
    if None in (ihard, icancel, iinterrupt, iterminal) or not (
            ihard < icancel < iinterrupt < iterminal):
        raise ValueError("invalidation/cancel/terminal order mismatch")
    inv = ie[ihard]
    if inv.get("reason") != "health:below_hard_minimum" or inv.get(
            "grants_input_authority") is not False:
        raise ValueError("invalidation disposition mismatch")
    observed_pending = [row for row in ie if row["event"] == "monitor_received"]
    if (not observed_pending or
            any(row.get("future_pending") is not True for row in observed_pending)):
        raise ValueError("invalidation was not observed while planner pending")
    if invalid["terminal"].get("status") != "cancelled":
        raise ValueError("cancellation terminal status mismatch")
    if invalid["terminal"].get("release") != {
            "verified": True, "keys_down": [], "buttons_down": []}:
        raise ValueError("cancellation terminal must verify empty release")
    if invalid["submitted"] != []:
        raise ValueError("invalidation path must not renew cover")
    return True


def main():
    result = json.loads((HERE / "RESULT.json").read_text(encoding="utf-8"))
    raw = [json.loads(line) for line in
           (HERE / "events.jsonl").read_text(encoding="utf-8").splitlines()]
    validate(result, raw)
    audit = {"schema": "issue59-v39-observation-pump-full-loop-audit-v1",
             "status": "PASS_FULL_LOOP_CONSTRUCTION",
             "frozen_main": FREEZE["main_commit"],
             "event_rows": len(raw),
             "result_sha256": hashlib.sha256((HERE / "RESULT.json").read_bytes()).hexdigest(),
             "events_sha256": hashlib.sha256((HERE / "events.jsonl").read_bytes()).hexdigest(),
             "checks": {"frozen_sources": True, "healthy_pending_observations": True,
                        "renewal_stopped_after_completion": True,
                        "hard_invalidation_cancelled_before_interrupt": True,
                        "cancel_terminal_verified_empty": True}}
    path = HERE / "AUDIT.json"
    if path.exists():
        raise FileExistsError(f"refusing to overwrite {path}")
    path.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(audit, separators=(",", ":")))


if __name__ == "__main__":
    main()
