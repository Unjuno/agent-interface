"""Candidate adapter checker for the real Tk widget transfer study."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from fixture import DisposableWidgetFixture


def _digest(value: object) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _semantic(view: dict) -> tuple:
    return (view["field"], view["value"], view["status_label"], view["completion"])


def _route(case: dict, direct_probe: bool = False) -> dict:
    app = DisposableWidgetFixture(case)
    try:
        if case.get("precondition") == "focus_decoy":
            app.focus("decoy")
        else:
            app.focus("checked" if case["kind"] == "set_checked" else "primary")
        before = app.public_view(case["target"])
        if case.get("precondition") == "stale_epoch":
            app.advance_epoch()

        stale = before["epoch"] != app.epoch
        focus_ambiguous = case.get("precondition") == "focus_decoy" and before["focus"] != case["target"]
        not_applicable = case["kind"] == "increment_button"
        if stale or focus_ambiguous or not_applicable:
            decision = dict(before)
        elif case["kind"] == "set_checked":
            app.issue_checked(bool(case["requests"][0]))
            decision = app.public_view("checked")
        elif case["kind"] == "set_text":
            for request in case["requests"]:
                app.issue_text(case["target"], request)
                current = app.public_view(case["target"])
                if case.get("precondition") == "pending_decision" and current["completion"] == "pending":
                    break
            decision = app.public_view(case["target"])
        else:
            raise ValueError("unsupported frozen operation")

        pending_at_decision = decision["completion"] != "complete"
        if case.get("precondition") == "wait_for_completion":
            app.wait_for_completion()
            decision = app.public_view(case["target"])
            pending_at_decision = False
        elif pending_at_decision:
            app.wait_for_completion()

        final = app.public_view(case["target"])
        laws = None
        baseline = None
        direct_view = None
        raw = None
        if not (stale or focus_ambiguous or not_applicable or pending_at_decision):
            if case["kind"] == "set_checked":
                get_put = decision["value"] == case["expected"]
                put_get = decision["value"] == case["expected"] and decision["status_label"] == "Applied once"
                put_put = put_get
                final_label = decision["value"] == case["expected"]
            else:
                # Get–Put: setting the currently observed value must preserve semantic state.
                before_get = app.public_view(case["target"])
                app.issue_text(case["target"], before_get["value"])
                after_get = app.public_view(case["target"])
                get_put = _semantic(before_get) == _semantic(after_get)

                # Put–Put: repeating the requested value cannot add an effect.
                before_put = app.public_view(case["target"])
                app.issue_text(case["target"], case["requests"][-1])
                after_put = app.public_view(case["target"])
                put_put = _semantic(before_put) == _semantic(after_put)
                final = after_put
                put_get = (final["value"] == case["expected"]
                           and final["status_label"] in {"Applied once", "Ready"}
                           and final["completion"] == "complete")
                final_label = final["value"] == case["expected"]

            laws = {"get_put": bool(get_put), "put_get": bool(put_get), "put_put": bool(put_put)}
            baseline = {"final_label_only": bool(final_label), "replay_consistency": None}

        raw = app.raw_snapshot()
        if case["kind"] == "set_text" and len(case["requests"]) > 1 and not direct_probe:
            app.close()
            direct_case = dict(case, requests=[case["requests"][-1]])
            direct_view = _route(direct_case, direct_probe=True)["final"]
            put_put = _semantic(final) == _semantic(direct_view)
            if laws is not None:
                laws["put_put"] = bool(put_put)

        if stale:
            status, reason = "UNKNOWN", "STALE_EPOCH"
        elif focus_ambiguous:
            status, reason = "UNKNOWN", "FOCUS_AMBIGUOUS"
        elif not_applicable:
            status, reason = "NOT_APPLICABLE", "NON_IDEMPOTENT_OPERATION"
        elif pending_at_decision:
            status, reason = "UNKNOWN", "COMPLETION_PENDING"
        else:
            status = "PASS" if all(laws.values()) else "VIOLATION"
            reason = None if status == "PASS" else "SCOPED_REAL_WIDGET_LAW_VIOLATION"

        return {"id": case["id"], "status": status, "reason": reason, "laws": laws,
                "baselines": baseline, "before": before, "decision_view": decision, "final": final,
                "direct_probe": direct_view, "raw": raw}
    finally:
        app.close()


def _replay_signature(row: dict) -> tuple:
    raw = row["raw"]
    return (raw["widget_values"], raw["checked"], raw["status_label"], raw["completion"])


def run(fixture: dict) -> dict:
    rows = []
    for case in fixture["cases"]:
        row = _route(case)
        replay = _route(case)
        if row["baselines"] is not None:
            row["baselines"]["replay_consistency"] = _replay_signature(row) == _replay_signature(replay)
        row["replay_raw"] = replay["raw"]
        rows.append(row)
    return {"schema": "lens-law-real-tk-candidate-v1", "input_sha256": _digest(fixture), "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", default="input.json")
    parser.add_argument("--output", default="results/candidate_raw.json")
    args = parser.parse_args()
    fixture = json.loads(Path(args.input).read_text(encoding="utf-8"))
    destination = Path(args.output)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(run(fixture), stream, sort_keys=True, separators=(",", ":"))
        stream.write("\n")
    print(json.dumps({"cases": len(fixture["cases"]), "status": "CANDIDATE_COMPLETE"},
                     sort_keys=True, separators=(",", ":")))


if __name__ == "__main__":
    main()
