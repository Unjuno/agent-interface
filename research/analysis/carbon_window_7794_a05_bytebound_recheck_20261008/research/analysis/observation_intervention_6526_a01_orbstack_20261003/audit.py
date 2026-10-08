"""Independent raw-only reconstruction for the Issue #6526 allocation."""
from __future__ import annotations

import json
import math
from collections import Counter, defaultdict
from pathlib import Path


def _jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line]


def exact_mcnemar_one_sided(control: list[bool], treated: list[bool]) -> float:
    if len(control) != len(treated):
        raise ValueError("paired vectors differ in length")
    treated_only_miss = sum(c and not t for c, t in zip(control, treated))
    reverse = sum((not c) and t for c, t in zip(control, treated))
    discordant = treated_only_miss + reverse
    if discordant == 0:
        return 1.0
    return sum(math.comb(discordant, k) for k in range(treated_only_miss, discordant+1)) / (2**discordant)


def audit(output: Path, expected_trials: list[dict]) -> dict:
    output = Path(output)
    errors: list[str] = []
    events_path = output / "app-events.jsonl"
    if not events_path.is_file():
        return {"decision": "STOP_AUDIT_ERRORS", "errors": ["missing-app-events"]}
    events = _jsonl(events_path)
    kinds: dict[str, list[dict]] = defaultdict(list)
    for event in events:
        kinds[event.get("kind", "<missing>")].append(event)
    starts = {event.get("trial_id"): event for event in kinds["trial_start"]}
    actions = Counter(event.get("trial_id") for event in kinds["action_effect"])
    deadline_events = {event.get("trial_id"): event for event in kinds["deadline_observed"]}
    expected_ids = [row["trial_id"] for row in expected_trials]
    if len(expected_ids) != len(set(expected_ids)) or len(starts) != len(kinds["trial_start"]) or set(starts) != set(expected_ids):
        errors.append("trial-start-set-mismatch")
    if len(deadline_events) != len(kinds["deadline_observed"]):
        errors.append("duplicate-deadline-event")
    if set(actions) - set(expected_ids):
        errors.append("unexpected-action-trial-id")
    if any(actions[tid] != 1 for tid in expected_ids):
        errors.append("action-count-not-exactly-one")
    if set(deadline_events) != set(expected_ids) or len(deadline_events) != len(kinds["deadline_observed"]):
        errors.append("deadline-set-mismatch")
    captures = Counter(event.get("trial_id") for event in kinds["screenshot"])
    sham_ticks = Counter(event.get("trial_id") for event in kinds["sham"])
    if kinds["screenshot_error"]:
        errors.append("screenshot-capture-error")
    outcomes: dict[str, bool] = {}
    for row in expected_trials:
        tid = row["trial_id"]
        try:
            raw = json.loads((output / f"deadline-{tid}.json").read_text())
        except (OSError, json.JSONDecodeError):
            errors.append(f"missing-or-invalid-deadline:{tid}")
            continue
        event = deadline_events.get(tid)
        if event is None or event.get("deadline_ns") != raw.get("deadline_ns"):
            errors.append(f"deadline-event-mismatch:{tid}")
        start_event = starts.get(tid)
        action_events = [item for item in kinds["action_effect"] if item.get("trial_id") == tid]
        if start_event is None or len(action_events) != 1:
            continue
        action = action_events[0]
        deadline_ns = start_event.get("start_ns", 0) + row["deadline_ms"] * 1_000_000
        if (start_event.get("block") != row["block"] or start_event.get("arm") != row["arm"]
                or start_event.get("schedule") != row["schedule"]):
            errors.append(f"trial-start-metadata-mismatch:{tid}")
        if action.get("action") != "button.invoke" or action.get("effect_path") != f"effect-{tid}.json":
            errors.append(f"action-metadata-mismatch:{tid}")
        if action.get("action_ns", 0) > deadline_ns:
            errors.append(f"action-late:{tid}")
        if action.get("action_ns", 0) - start_event.get("start_ns", 0) != row["action_delay_ms"] * 1_000_000:
            errors.append(f"action-delay-mismatch:{tid}")
        if action.get("persisted_ns", 0) < action.get("action_ns", 0):
            errors.append(f"invalid-persist-time:{tid}")
        if raw.get("deadline_ns") != deadline_ns:
            errors.append(f"deadline-not-bound-to-start:{tid}")
        if raw.get("trial_id") != tid or raw.get("snapshot_ns", 0) < raw.get("deadline_ns", 0):
            errors.append(f"invalid-independent-clock:{tid}")
        effect_path = output / f"effect-{tid}.json"
        payload = raw.get("effect_payload")
        if raw.get("effect_present") is True and not effect_path.is_file():
            errors.append(f"oracle-payload-without-file:{tid}")
        if effect_path.exists():
            persisted = json.loads(effect_path.read_text())
            if persisted != payload and raw.get("effect_present") is True:
                errors.append(f"oracle-payload-disagrees:{tid}")
        valid_effect = (isinstance(payload, dict) and payload.get("trial_id") == tid
                        and payload.get("value") == row["expected_value"])
        outcomes[tid] = bool(valid_effect and raw.get("effect_present") is True)
        if row["arm"] == "SCREENSHOT" and captures[tid] == 0:
            errors.append(f"no-screenshot:{tid}")
        if row["arm"] == "SHAM" and sham_ticks[tid] == 0:
            errors.append(f"no-sham:{tid}")
        if row["arm"] == "MINIMAL" and (captures[tid] or sham_ticks[tid]):
            errors.append(f"minimal-arm-contaminated:{tid}")

    counts = Counter((r["block"], r["schedule"], r["arm"]) for r in expected_trials)
    block_ids = sorted({r["block"] for r in expected_trials})
    conditions = [(b, s, a) for b in block_ids for s in ("SENSITIVE", "STABLE")
                  for a in ("MINIMAL", "SCREENSHOT", "SHAM")]
    if (len(expected_trials) != 180 or block_ids != list(range(1, 31))
            or any(counts[c] != 1 for c in conditions)):
        errors.append("allocation-not-balanced")
    observed_order = [event.get("trial_id") for event in kinds["trial_start"]]
    if observed_order != expected_ids:
        errors.append("execution-order-mismatch")
    if any(r.get("action_delay_ms") != 90 for r in expected_trials):
        errors.append("action-policy-changed")

    rates: dict[str, dict] = {}
    if len(outcomes) == 180 and not errors:
        for schedule in ("SENSITIVE", "STABLE"):
            for arm in ("MINIMAL", "SCREENSHOT", "SHAM"):
                rows = [r for r in expected_trials if r["schedule"] == schedule and r["arm"] == arm]
                misses = sum(not outcomes[r["trial_id"]] for r in rows)
                rates[f"{schedule}/{arm}"] = {"n": len(rows), "misses": misses, "miss_rate": misses/len(rows)}
    stable_ok = len(outcomes) == 180 and all(rates.get(f"STABLE/{arm}", {}).get("misses", 30) <= 1
                    for arm in ("MINIMAL", "SCREENSHOT", "SHAM"))
    p_minimal = p_sham = delta_minimal = delta_sham = None
    if len(outcomes) == 180 and not errors:
        pairs: dict[int, dict[str, bool]] = defaultdict(dict)
        for row in expected_trials:
            if row["schedule"] == "SENSITIVE":
                pairs[row["block"]][row["arm"]] = outcomes[row["trial_id"]]
        screen = [pairs[b]["SCREENSHOT"] for b in sorted(pairs)]
        minimal = [pairs[b]["MINIMAL"] for b in sorted(pairs)]
        sham = [pairs[b]["SHAM"] for b in sorted(pairs)]
        if len(screen) == 30:
            p_minimal = exact_mcnemar_one_sided(minimal, screen)
            p_sham = exact_mcnemar_one_sided(sham, screen)
            delta_minimal = (sum(not v for v in screen)-sum(not v for v in minimal))/30
            delta_sham = (sum(not v for v in screen)-sum(not v for v in sham))/30
        else:
            errors.append("sensitive-pair-count-mismatch")
    try:
        candidate = json.loads((output / "candidate-receipt.json").read_text())
    except (OSError, json.JSONDecodeError):
        candidate = {}
    if candidate.get("exit_code") != 0 or candidate.get("trial_count") != len(expected_trials):
        errors.append("candidate-receipt-invalid")
    if errors:
        decision = "STOP_AUDIT_ERRORS"
    elif not stable_ok:
        decision = "HOLD_STABLE_CONTROL_GATE"
    elif min(delta_minimal, delta_sham) >= 0.20 and p_minimal <= 0.05 and p_sham <= 0.05:
        decision = "H_PASS_SCOPED"
    else:
        decision = "H_FAIL_SCOPED"
    return {"decision": decision, "errors": errors, "stable_control_gate": stable_ok,
            "rates": rates, "sensitive_miss_rate_delta_screenshot_minus_minimal": delta_minimal,
            "sensitive_miss_rate_delta_screenshot_minus_sham": delta_sham,
            "sensitive_mcnemar_one_sided_p_screenshot_vs_minimal": p_minimal,
            "sensitive_mcnemar_one_sided_p_screenshot_vs_sham": p_sham,
            "capture_count": sum(captures.values()), "sham_tick_count": sum(sham_ticks.values()),
            "trial_count": len(expected_trials)}
