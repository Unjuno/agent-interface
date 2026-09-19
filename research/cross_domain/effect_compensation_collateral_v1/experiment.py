from __future__ import annotations

import argparse
import json
from pathlib import Path

from receiver import connect, commit_event

INITIAL = ("old", "preserve")
TARGET = ("target", "preserve")
WRONG = ("wrong", "preserve")
CLEAN_RESTORE = ("old", "preserve")
COLLATERAL_DAMAGE = ("old", "damaged")

VERIFIED = "EFFECT_VERIFIED"
COMPENSATED = "EFFECT_CONTRADICTED_COMPENSATED"
INCOMPLETE = "EFFECT_CONTRADICTED_COMPENSATION_INCOMPLETE"


def primary_only_label(state: tuple[str, str], history: list[dict]) -> str:
    first = history[0]
    if first["primary"] == TARGET[0] and first["collateral"] == TARGET[1]:
        return VERIFIED
    if state[0] == INITIAL[0]:
        return COMPENSATED
    return INCOMPLETE


def full_invariant_label(state: tuple[str, str], history: list[dict]) -> str:
    first = history[0]
    if first["primary"] == TARGET[0] and first["collateral"] == TARGET[1]:
        return VERIFIED
    if state == INITIAL:
        return COMPENSATED
    return INCOMPLETE


def expected_truth(scenario: str) -> str:
    return {
        "correct": VERIFIED,
        "wrong_compensated_clean": COMPENSATED,
        "wrong_compensated_collateral": INCOMPLETE,
    }[scenario]


def run_case(root: Path, case: dict) -> dict:
    case_dir = root / case["id"]
    case_dir.mkdir(parents=True, exist_ok=False)
    db_path = case_dir / "state.sqlite"
    conn = connect(db_path)
    scenario = case["scenario"]
    if scenario == "correct":
        commit_event(conn, "effect", *TARGET)
    elif scenario == "wrong_compensated_clean":
        commit_event(conn, "effect", *WRONG)
        commit_event(conn, "compensation", *CLEAN_RESTORE)
    elif scenario == "wrong_compensated_collateral":
        commit_event(conn, "effect", *WRONG)
        commit_event(conn, "compensation", *COLLATERAL_DAMAGE)
    else:
        raise ValueError(f"unknown scenario: {scenario}")

    state_row = conn.execute(
        "SELECT primary_value,collateral_value FROM state WHERE id=1"
    ).fetchone()
    event_rows = conn.execute(
        "SELECT seq,kind,primary_value,collateral_value FROM events ORDER BY seq"
    ).fetchall()
    conn.close()
    state = (state_row[0], state_row[1])
    history = [
        {"seq": seq, "kind": kind, "primary": primary, "collateral": collateral}
        for seq, kind, primary, collateral in event_rows
    ]
    truth = expected_truth(scenario)
    primary = primary_only_label(state, history)
    full = full_invariant_label(state, history)
    row = {
        "id": case["id"],
        "scenario": scenario,
        "state": {"primary": state[0], "collateral": state[1]},
        "history": history,
        "truth": truth,
        "primary_only": primary,
        "full_invariant": full,
        "primary_truthful": primary == truth,
        "full_truthful": full == truth,
    }
    (case_dir / "row.json").write_text(json.dumps(row, indent=2, sort_keys=True) + "\n")
    return row


def summarize(rows: list[dict]) -> dict:
    by_scenario = {}
    for scenario in sorted({row["scenario"] for row in rows}):
        group = [row for row in rows if row["scenario"] == scenario]
        by_scenario[scenario] = {
            "count": len(group),
            "primary_truthful": sum(row["primary_truthful"] for row in group),
            "full_truthful": sum(row["full_truthful"] for row in group),
            "primary_labels": sorted({row["primary_only"] for row in group}),
            "full_labels": sorted({row["full_invariant"] for row in group}),
            "final_states": sorted({(row["state"]["primary"], row["state"]["collateral"]) for row in group}),
        }
    return {
        "schema": "effect-compensation-collateral-result-v1",
        "task": "EFFECT-COMPENSATION-COLLATERAL-20260916-001",
        "formal_cases": len(rows),
        "primary_only_truthful_count": sum(row["primary_truthful"] for row in rows),
        "full_invariant_truthful_count": sum(row["full_truthful"] for row in rows),
        "by_scenario": by_scenario,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--evidence", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()
    plan = json.loads(args.plan.read_text())
    args.evidence.mkdir(parents=True, exist_ok=False)
    rows = [run_case(args.evidence, case) for case in plan["cases"]]
    result = summarize(rows)
    result["rows"] = rows
    args.result.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
