"""Independent raw-only reconstruction for Issue #8319; imports no candidate code."""
from __future__ import annotations

import json
import sys
from pathlib import Path

PATCH_SPACE = tuple([f"case:{n}" for n in range(8)] + [f"stratum:{n}" for n in range(4)])


def make_cases(seed: int, cohort_tag: str) -> list[tuple[str, int, bool]]:
    return [(f"{cohort_tag}{seed:03d}-{j:02d}", (j + seed) % 4,
             ((j * 3 + seed) % 5) not in (0, 1)) for j in range(32)]


def covered(case: tuple[str, int, bool], patch: str) -> bool:
    identity, group, _ = case
    if patch.startswith("case:"):
        return not identity.startswith("F") and int(identity.rsplit("-", 1)[1]) == int(patch[5:])
    return group == int(patch[8:])


def tally(cases: list[tuple[str, int, bool]], edits: list[str]) -> tuple[int, int]:
    n_ok = 0
    for identity, group, native in cases:
        repaired = any(covered((identity, group, native), edit) for edit in edits)
        n_ok += int(native or repaired)
    return n_ok, len(cases)


def raw_feedback(mode: str, cases: list[tuple[str, int, bool]], edits: list[str]) -> dict:
    failures = [(identity, group) for identity, group, native in cases
                if not native and not any(covered((identity, group, native), p) for p in edits)]
    ok, total = tally(cases, edits)
    record = {"kind": mode, "aggregate_correct": ok, "aggregate_total": total}
    if mode == "FULL":
        record["error_ids"] = [identity for identity, _ in failures]
        record["error_by_stratum"] = {str(k): sum(group == k for _, group in failures) for k in range(4)}
    else:
        record["improvement_over_previous"] = None
        record["threshold_met"] = False
    return record


def deterministic_selector(rule: str, feedback_record: dict, used: list[str], step: int) -> str:
    remaining = [p for p in PATCH_SPACE if p not in used]
    if rule == "CASE_PATCH":
        informative = [f"case:{int(token.rsplit('-', 1)[1])}" for token in feedback_record.get("error_ids", [])]
    else:
        histogram = feedback_record.get("error_by_stratum", {})
        informative = [f"stratum:{g}" for g in sorted(range(4), key=lambda g: (-int(histogram.get(str(g), 0)), g))]
    order = informative + list(PATCH_SPACE[step:] + PATCH_SPACE[:step])
    return next(item for item in order if item in remaining)


def expected(seed: int, mode: str, rule: str) -> dict:
    dev = make_cases(seed, "D")
    fresh = make_cases(seed, "F")
    selected: list[str] = []
    entries: list[dict] = []
    prior = tally(dev, selected)[0]
    latest = raw_feedback(mode, dev, selected)
    first_feedback = latest.copy()
    for step in range(4):
        if step == 2:
            entries.append({"round": step, "proposal": "safety_regression", "safety_event": True,
                            "disclosed_exactly": True, "veto": True, "fresh_read": False})
            continue
        choice = deterministic_selector(rule, latest, selected, step)
        selected.append(choice)
        current = tally(dev, selected)[0]
        disclosure = raw_feedback(mode, dev, selected)
        if mode == "CONTROLLED":
            gain = current - prior
            disclosure["improvement_over_previous"] = gain
            disclosure["threshold_met"] = gain >= 1
            disclosure.pop("error_ids", None)
            disclosure.pop("error_by_stratum", None)
        prior, latest = current, disclosure
        entries.append({"round": step, "proposal": choice, "feedback": disclosure,
                        "safety_event": False, "veto": False, "fresh_read": False})
    d_ok, d_n = tally(dev, selected)
    f_ok, f_n = tally(fresh, selected)
    return {"seed": seed, "feedback": mode, "updater": rule, "query_count": 5,
            "patches": selected, "trace": entries, "candidate_locked_before_fresh": True,
            "initial_feedback": first_feedback,
            "dev_correct": d_ok, "dev_total": d_n, "fresh_correct": f_ok, "fresh_total": f_n,
            "optimism": d_ok / d_n - f_ok / f_n,
            "safety_veto_count": sum(int(item["veto"]) for item in entries),
            "raw_released_after_lock": True}


def reconstruct(rows: list[dict]) -> list[str]:
    errors = []
    keys = [(s, f, u) for s in range(100) for f in ("FULL", "CONTROLLED")
            for u in ("CASE_PATCH", "STRATUM_PATCH")]
    if len(rows) != len(keys):
        return [f"row_count:{len(rows)}!={len(keys)}"]
    for i, key in enumerate(keys):
        want = expected(*key)
        if rows[i] != want:
            errors.append(f"row_{i}_reconstruction_mismatch")
    return errors


def mutation_checks(rows: list[dict]) -> list[str]:
    controls: list[tuple[str, list[dict]]] = []
    import copy
    def changed(label: str, mutate) -> None:
        altered = copy.deepcopy(rows)
        mutate(altered[0])
        controls.append((label, altered))
    changed("feedback_swap", lambda r: r.__setitem__("feedback", "CONTROLLED"))
    changed("updater_swap", lambda r: r.__setitem__("updater", "STRATUM_PATCH"))
    changed("early_fresh", lambda r: r.__setitem__("candidate_locked_before_fresh", False))
    changed("missing_safety_veto", lambda r: r["trace"][2].__setitem__("disclosed_exactly", False))
    changed("cohort_change", lambda r: r.__setitem__("fresh_total", r["fresh_total"] - 1))
    changed("forged_feedback", lambda r: r["trace"][0]["feedback"].__setitem__("aggregate_correct", -1))
    return [name for name, altered in controls if not reconstruct(altered)]


def main(input_path: str, output_path: str) -> None:
    rows = json.loads(Path(input_path).read_text(encoding="utf-8"))
    errors = reconstruct(rows)
    rejected = mutation_checks(rows)
    audit_record = {"status": "PASS" if not errors and len(rejected) == 6 else "FAIL",
                    "rows": len(rows), "checks": len(rows), "errors": errors,
                    "mutation_controls": 6, "mutations_rejected": rejected}
    Path(output_path).write_text(json.dumps(audit_record, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
    if audit_record["status"] != "PASS":
        raise SystemExit(1)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: audit.py RAW.json AUDIT.json")
    main(sys.argv[1], sys.argv[2])
