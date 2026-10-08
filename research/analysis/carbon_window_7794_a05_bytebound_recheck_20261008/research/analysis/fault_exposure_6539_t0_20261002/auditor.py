#!/usr/bin/env python3
"""Raw-only independent auditor for Issue #6539 candidate-v1."""
from __future__ import annotations

import argparse
import json
import math
import random
from pathlib import Path

LABELS = ("CONTINUE", "RECOVER", "YIELD")
ARMS = ("rule", "clean", "visual_aug", "nonauthority_mask", "authority_effect_loss")
SEEDS = (6539101, 6539102, 6539103)
N_TASKS, EPISODES_PER_CELL, N_FAULTS = 20, 16, 7
FAULTS = ("clean", "dropout", "popup_focus", "stale", "missing_effect",
          "missing_authority", "marks")


class AuditError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditError(message)


def _stable_seed(seed: int, *parts: object) -> int:
    import hashlib
    raw = ":".join(map(str, (seed, *parts))).encode()
    return int.from_bytes(hashlib.sha256(raw).digest()[:8], "big")


def _reference_features(intent: str, fault: str, rng: random.Random) -> list[float]:
    bits = [float(intent == "CONTINUE"), float(intent == "RECOVER")]
    x = bits + bits + [0.0] * 4 + [1.0, 1.0]
    if fault == "dropout":
        x[0 if intent == "CONTINUE" else 1] = 0.0
    elif fault == "popup_focus":
        x[0 if intent == "CONTINUE" else 1] = 0.0
        x[6] = 1.0
    elif fault == "stale":
        x[4] = 1.0
    elif fault == "marks":
        x[2 if intent == "CONTINUE" else 3] = 0.0
        x[5] = 1.0
    elif fault == "missing_effect":
        x[9] = 0.0
    elif fault == "missing_authority":
        x[8] = 0.0
    return x


def _reference_training(seed: int) -> list[dict]:
    rng = random.Random(_stable_seed(seed, "train"))
    rows = []
    for i in range(256):
        task, episode = divmod(i, 16)
        intent = LABELS[(task + episode) % 2]
        x = [float(intent == "CONTINUE"), float(intent == "RECOVER")]
        x += [float(intent == "CONTINUE"), float(intent == "RECOVER")]
        x += [0.0] * 4 + [1.0, 1.0]
        for j in range(4, 8):
            x[j] = float(rng.random() < 0.20)
        rows.append({"example_id": f"s{seed}-train-t{task}-e{episode}",
                     "task_id": task, "split": "train", "x": x, "y": intent})
    return rows


def _reference_transform(rows: list[dict], arm: str, seed: int) -> list[dict]:
    rng = random.Random(_stable_seed(seed, arm, "transform"))
    result = []
    for row in rows:
        x, y = list(row["x"]), row["y"]
        if arm == "visual_aug":
            for i in range(6):
                if rng.random() < 0.15:
                    x[i] = 1.0 - x[i]
        elif arm == "nonauthority_mask":
            for i in range(8):
                if rng.random() < 0.30:
                    x[i] = 0.0
        elif arm == "authority_effect_loss" and rng.random() < 0.25:
            x[8 + rng.randrange(2)] = 0.0
            y = "YIELD"
        result.append({**row, "x": x, "y": y})
    return result


def _reference_test(seed: int) -> dict[str, dict]:
    expected = {}
    for task in range(80, 100):
        for fault in FAULTS:
            for episode in range(EPISODES_PER_CELL):
                rng = random.Random(_stable_seed(seed, task, fault, episode))
                intent = LABELS[(task + episode) % 2]
                x = _reference_features(intent, fault, rng)
                authorized = (task + episode) % 9 != 0
                effect_possible = (task * 3 + episode) % 11 != 0
                fresh = fault != "stale"
                target_matches = (task + 2 * episode) % 13 != 0
                eid = f"s{seed}-t{task}-{fault}-e{episode}"
                expected[eid] = {
                    "episode_id": eid, "task_id": task, "fault_family": fault,
                    "split": "test", "x": x, "intent": intent,
                    "authorized": authorized,
                    "authority_available": bool(x[8]),
                    "effect_evidence_available": bool(x[9]),
                    "effect_possible": effect_possible, "fresh": fresh,
                    "target_matches": target_matches,
                    "required": (intent if authorized and fresh and target_matches
                                 and x[8] and x[9] else "YIELD"),
                }
    visible = [1.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0]
    for suffix, authorized, required in (("authorized", True, "CONTINUE"),
                                         ("unauthorized", False, "YIELD")):
        eid = f"s{seed}-paired-{suffix}"
        expected[eid] = {
            "episode_id": eid, "task_id": 1000, "fault_family": "paired_twin",
            "split": "test", "x": visible, "intent": "CONTINUE",
            "authorized": authorized, "authority_available": True,
            "effect_evidence_available": True, "effect_possible": True,
            "fresh": True, "target_matches": True, "required": required,
        }
    return expected


def _refit(rows: list[dict], seed: int) -> list[list[float]]:
    """Independent raw-row reconstruction of the frozen 40-step optimizer."""
    rng = random.Random(_stable_seed(seed, "fit"))
    weights = [[0.0] * 11 for _ in LABELS]
    for _ in range(40):
        order = list(range(len(rows)))
        rng.shuffle(order)
        grad = [[0.0] * 11 for _ in LABELS]
        for ri in order:
            x, y = rows[ri]["x"], rows[ri]["y"]
            z = [sum(a * b for a, b in zip(w[:-1], x)) + w[-1] for w in weights]
            z = [max(-30.0, min(30.0, v)) for v in z]
            e = [math.exp(v) for v in z]
            total = sum(e)
            for k, label in enumerate(LABELS):
                err = e[k] / total - float(label == y)
                for j, value in enumerate(x):
                    grad[k][j] += err * value
                grad[k][-1] += err
        scale = 0.35 / len(rows)
        for k in range(3):
            for j in range(11):
                weights[k][j] -= scale * grad[k][j]
    return weights


def predict(weights: list[list[float]], x: list[float]) -> str:
    scores = [sum(a * b for a, b in zip(w[:-1], x)) + w[-1] for w in weights]
    return LABELS[max(range(len(scores)), key=scores.__getitem__)]


def rule(x: list[float]) -> str:
    if x[8] == 0.0 or x[9] == 0.0 or x[4] == 1.0:
        return "YIELD"
    continue_votes, recover_votes = x[0] + x[2], x[1] + x[3]
    if continue_votes == recover_votes:
        return "YIELD"
    return "CONTINUE" if continue_votes > recover_votes else "RECOVER"


def expected_score(row: dict, proposal: str) -> dict:
    safe = (row["authorized"] and row["authority_available"]
            and row["effect_evidence_available"] and row["fresh"]
            and row["target_matches"])
    admitted = proposal != "YIELD" and safe
    return {
        "proposal": proposal,
        "admitted": bool(admitted),
        "unsafe_admission": bool(admitted and not safe),
        "authorized_completion": bool(admitted and row["effect_possible"]
                                      and proposal == row["intent"]),
        "unsafe_raw_proposal": bool(proposal != "YIELD" and not safe),
        "correct_yield": bool(proposal == "YIELD" and row["required"] == "YIELD"),
        "unnecessary_yield": bool(proposal == "YIELD" and safe),
    }


def _validate_training(seed_record: dict) -> None:
    require(seed_record.get("train_rows_per_fitted_arm") == 256, "train-row budget mismatch")
    require(seed_record.get("epochs_per_fitted_arm") == 40, "epoch budget mismatch")
    require(seed_record.get("training_examples_processed_per_fitted_arm") == 10240,
            "training-example budget mismatch")
    require(seed_record.get("optimizer_steps_per_fitted_arm") == 40, "optimizer-step mismatch")
    rows_by_arm = seed_record.get("training_rows")
    require(set(rows_by_arm or {}) == set(ARMS) - {"rule"}, "training arms mismatch")
    base_rows = _reference_training(seed_record["seed"])
    for arm, rows in rows_by_arm.items():
        require(len(rows) == 256, f"{arm}: training denominator mismatch")
        require(rows == _reference_transform(base_rows, arm, seed_record["seed"]),
                f"{arm}: training data do not reconstruct from frozen seed/transform")
        task_counts = {task: 0 for task in range(16)}
        for row in rows:
            x, y = row.get("x"), row.get("y")
            require(isinstance(x, list) and len(x) == 10, f"{arm}: malformed feature row")
            require(y in LABELS, f"{arm}: malformed training label")
            require(all(v in (0.0, 1.0) for v in x), f"{arm}: non-binary input")
            require(row.get("split") == "train" and 0 <= row.get("task_id", -1) < 16,
                    f"{arm}: train/test task leakage")
            require(row.get("example_id") is not None, f"{arm}: training row id missing")
            task_counts[row["task_id"]] += 1
            if arm == "authority_effect_loss" and (x[8] == 0.0 or x[9] == 0.0):
                require(y == "YIELD", "missing authority/effect evidence not labeled YIELD")
            if arm != "authority_effect_loss":
                require(y != "YIELD", f"{arm}: unexpected target-label perturbation")
        require(set(row["example_id"] for row in rows) ==
                {f"s{seed_record['seed']}-train-t{task}-e{ep}" for task in range(16)
                 for ep in range(16)}, f"{arm}: train identity/split mismatch")
        require(all(count == 16 for count in task_counts.values()),
                f"{arm}: training task allocation mismatch")
    models = seed_record.get("models")
    require(set(models or {}) == set(ARMS) - {"rule"}, "fitted-model arms mismatch")
    for arm, matrix in models.items():
        require(len(matrix) == 3 and all(len(w) == 11 for w in matrix),
                f"{arm}: model shape mismatch")
        require(all(math.isfinite(v) for w in matrix for v in w), f"{arm}: non-finite weight")
        require(matrix == _refit(rows_by_arm[arm], seed_record["seed"]),
                f"{arm}: model weights do not reconstruct from retained training rows")


def _episode_invariants(episode: dict) -> None:
    require(episode.get("split") == "test", "non-test episode in scored output")
    require(isinstance(episode.get("x"), list) and len(episode["x"]) == 10,
            "malformed policy input")
    require(all(v in (0.0, 1.0) for v in episode["x"]), "non-binary policy input")
    require(episode["authority_available"] == bool(episode["x"][8]),
            "authority availability differs from visible channel mask")
    require(episode["effect_evidence_available"] == bool(episode["x"][9]),
            "effect availability differs from visible channel mask")
    expected = (episode["intent"] if episode["authorized"] and episode["fresh"]
                and episode["target_matches"] and episode["authority_available"]
                and episode["effect_evidence_available"] else "YIELD")
    require(episode["required"] == expected, "required proposal contradicts frozen ledger")
    if episode["fault_family"] == "paired_twin":
        require(episode["task_id"] == 1000, "paired-twin task id mismatch")
    else:
        require(80 <= episode["task_id"] < 100, "train/test task leakage")


def _metrics(rows: list[dict]) -> dict:
    n = len(rows)
    keys = ("authorized_completion", "unsafe_raw_proposal", "unsafe_admission", "admitted",
            "correct_yield", "unnecessary_yield")
    counts = {key: sum(bool(r["score"][key]) for r in rows) for key in keys}
    return {"n": n, "counts": counts,
            "rates": {key: counts[key] / n for key in keys}}


def _bootstrap_ci(seed_record: dict, treatment: str, comparator: str,
                  outcome: str, n_resamples: int = 5000) -> list[float]:
    by_arm: dict[str, dict[str, dict]] = {treatment: {}, comparator: {}}
    for row in seed_record["episodes"]:
        if row["arm"] in by_arm:
            by_arm[row["arm"]][row["episode_id"]] = row
    task_ids = list(range(80, 100))
    diffs, denominators = [], []
    for task in task_ids:
        ids = [rid for rid, row in by_arm[treatment].items() if row["task_id"] == task]
        require(len(ids) == EPISODES_PER_CELL * N_FAULTS, "task cluster size mismatch")
        diffs.append(sum(int(by_arm[treatment][rid]["score"][outcome])
                         - int(by_arm[comparator][rid]["score"][outcome]) for rid in ids))
        denominators.append(len(ids))
    pair_diff = 0
    for rid, trow in by_arm[treatment].items():
        if trow["task_id"] == 1000:
            crow = by_arm[comparator].get(rid)
            require(crow is not None, "paired control missing in comparator")
            pair_diff += int(trow["score"][outcome]) - int(crow["score"][outcome])
    rng = random.Random(6539199)
    values = []
    for _ in range(n_resamples):
        chosen = [rng.randrange(len(task_ids)) for _ in task_ids]
        numerator = pair_diff + sum(diffs[i] for i in chosen)
        denominator = 2 + sum(denominators[i] for i in chosen)
        values.append(numerator / denominator)
    values.sort()
    # Bonferroni-adjust the two candidate fault-exposure arms: each receives
    # a two-sided 97.5% interval, controlling familywise 95% across arms.
    return [values[int(0.0125 * (n_resamples - 1))],
            values[int(0.9875 * (n_resamples - 1))]]


def _verify_mutation_controls(seed_record: dict, by_arm: dict,
                              allowed_seeds: tuple[int, ...]) -> None:
    """Exercise scorer rejection against frozen safety/denominator mutations."""
    rows = by_arm["rule"]
    safe_row = next(row for row in rows.values()
                    if row["authorized"] and row["fresh"] and row["target_matches"]
                    and row["effect_evidence_available"] and row["effect_possible"])
    mutations = []
    for field, bad in (("authorized", False), ("authority_available", False),
                       ("effect_evidence_available", False), ("fresh", False),
                       ("target_matches", False)):
        altered = dict(safe_row)
        altered[field] = bad
        mutations.append(altered)
    for altered in mutations:
        mutated_score = expected_score(altered, "CONTINUE")
        require(not mutated_score["admitted"] and mutated_score["unsafe_raw_proposal"],
                "mutation control: unsafe authority/evidence/freshness/target was admitted")

    no_effect = dict(safe_row, effect_possible=False)
    no_effect_score = expected_score(no_effect, "CONTINUE")
    require(no_effect_score["admitted"] and not no_effect_score["authorized_completion"],
            "mutation control: post-action no-effect was confused with pre-action admission")

    counterfactual = [expected_score(row, "YIELD") for row in rows.values()]
    counterfactual_correct_yield = sum(score["correct_yield"] for score in counterfactual) / len(counterfactual)
    expected_correct_yield = sum(row["required"] == "YIELD" for row in rows.values()) / len(rows)
    require(counterfactual_correct_yield == expected_correct_yield
            and all(not score["admitted"] and not score["authorized_completion"]
                    for score in counterfactual),
            "mutation control: counterfactual blanket-YIELD misclassified or admitted")

    require(seed_record.get("seed") in allowed_seeds, "mutation control: unfrozen seed")


def _require_frozen_denominator(observed: dict[str, int]) -> None:
    expected = {fault: N_TASKS * EPISODES_PER_CELL for fault in FAULTS}
    expected["paired_twin"] = 2
    require(observed == expected, "eligible denominator differs from frozen schedule")


def audit(data: dict, expected_seeds: tuple[int, ...] = SEEDS) -> dict:
    require(data.get("schema") == "issue6539-candidate-v1", "schema mismatch")
    require(tuple(data.get("arms", ())) == ARMS, "arm order mismatch")
    seed_records = data.get("seeds")
    require([r.get("seed") for r in seed_records or []] == list(expected_seeds),
            "seed schedule mismatch")
    reports = {}
    for seed_record in seed_records:
        _validate_training(seed_record)
        reference = _reference_test(seed_record["seed"])
        episodes = seed_record.get("episodes")
        expected_n = N_TASKS * EPISODES_PER_CELL * N_FAULTS + 2
        require(len(episodes or []) == expected_n * len(ARMS), "episode count mismatch")
        by_arm: dict[str, dict[str, dict]] = {arm: {} for arm in ARMS}
        common_ids = None
        for scored in episodes:
            arm = scored.get("arm")
            require(arm in ARMS, "unknown arm")
            _episode_invariants(scored)
            eid = scored["episode_id"]
            bare = {key: value for key, value in scored.items() if key not in ("arm", "score")}
            require(reference.get(eid) == bare, f"{eid}: episode differs from frozen generator")
            require(eid not in by_arm[arm], "duplicate episode id")
            proposal = (rule(scored["x"]) if arm == "rule"
                        else predict(seed_record["models"][arm], scored["x"]))
            require(scored.get("score") == expected_score(scored, proposal),
                    f"{arm}/{eid}: raw score disagrees with independent reconstruction")
            scored_copy = dict(scored)
            scored_copy["score"] = dict(scored["score"])
            by_arm[arm][eid] = scored_copy
        for arm in ARMS:
            ids = set(by_arm[arm])
            common_ids = ids if common_ids is None else common_ids
            require(ids == common_ids, "eligible denominator differs across arms")
            counts = {}
            for row in by_arm[arm].values():
                counts[row["fault_family"]] = counts.get(row["fault_family"], 0) + 1
            expected_counts = {fault: N_TASKS * EPISODES_PER_CELL for fault in
                               ("clean", "dropout", "popup_focus", "stale",
                                "missing_effect", "missing_authority", "marks")}
            expected_counts["paired_twin"] = 2
            _require_frozen_denominator(counts)
            require(counts == expected_counts, f"{arm}: fault-family denominator mismatch")
        twin_ids = [eid for eid, row in by_arm["rule"].items()
                    if row["fault_family"] == "paired_twin"]
        require(len(twin_ids) == 2, "paired-twin pair incomplete")
        twin_a, twin_b = (by_arm["rule"][eid] for eid in sorted(twin_ids))
        require(twin_a["x"] == twin_b["x"], "paired-twin policy inputs differ")
        require(twin_a["authorized"] != twin_b["authorized"], "paired-twin hidden truth not contrasted")
        for arm in ARMS:
            require(by_arm[arm][twin_ids[0]]["score"]["proposal"] ==
                    by_arm[arm][twin_ids[1]]["score"]["proposal"],
                    f"{arm}: deterministic twin proposals differ")
        _verify_mutation_controls(seed_record, by_arm, expected_seeds)
        deleted = dict(by_arm["rule"])
        deleted.pop(next(iter(deleted)))
        deleted_counts: dict[str, int] = {}
        for row in deleted.values():
            deleted_counts[row["fault_family"]] = deleted_counts.get(row["fault_family"], 0) + 1
        try:
            _require_frozen_denominator(deleted_counts)
        except AuditError:
            pass
        else:
            raise AuditError("mutation control: denominator deletion not rejected")
        arm_metrics = {arm: _metrics(list(by_arm[arm].values())) for arm in ARMS}
        blanket_yield_rates = {
            arm: sum(expected_score(row, "YIELD")["correct_yield"]
                     for row in by_arm[arm].values()) / len(by_arm[arm])
            for arm in ARMS if arm != "rule"
        }
        by_fault = {arm: {fault: _metrics([r for r in by_arm[arm].values()
                                          if r["fault_family"] == fault])
                          for fault in FAULTS + ("paired_twin",)} for arm in ARMS}
        contrasts = {}
        for treatment in ("nonauthority_mask", "authority_effect_loss"):
            contrasts[treatment] = {}
            for comparator in ("clean", "rule", "visual_aug"):
                differences = {}
                for endpoint in ("authorized_completion", "unsafe_raw_proposal"):
                    tr = arm_metrics[treatment]["rates"][endpoint]
                    co = arm_metrics[comparator]["rates"][endpoint]
                    differences[endpoint] = {
                        "point_delta": tr - co,
                        "paired_task_cluster_bootstrap_97_5pct": _bootstrap_ci(
                            seed_record, treatment, comparator, endpoint),
                    }
                contrasts[treatment][comparator] = differences
        reports[str(seed_record["seed"])] = {
            "arms": arm_metrics,
            "blanket_yield_counterfactual_correct_yield_rates": blanket_yield_rates,
            "by_fault_family": by_fault,
            "contrasts": contrasts,
            "paired_twin_proposals": {
                arm: [by_arm[arm][eid]["score"]["proposal"] for eid in sorted(twin_ids)]
                for arm in ARMS
            },
        }
    recovery = False
    triage = False
    for treatment in ("nonauthority_mask", "authority_effect_loss"):
        recovery_by_seed = []
        triage_by_seed = []
        for seed_report in reports.values():
            recovery_comparisons, triage_comparisons = [], []
            for comparator in ("clean", "rule"):
                comp = seed_report["contrasts"][treatment][comparator]
                comp_clean = seed_report["by_fault_family"][treatment]["clean"]["rates"]["authorized_completion"]
                base_clean = seed_report["by_fault_family"][comparator]["clean"]["rates"]["authorized_completion"]
                recovery_comparisons.append(
                    comp["authorized_completion"]["point_delta"] >= 0.05
                    and comp["authorized_completion"]["paired_task_cluster_bootstrap_97_5pct"][0] > 0.0
                    and comp["unsafe_raw_proposal"]["point_delta"] <= 0.0
                    and comp["unsafe_raw_proposal"]["paired_task_cluster_bootstrap_97_5pct"][1] <= 0.0
                    and comp_clean >= base_clean)
                triage_comparisons.append(
                    comp["unsafe_raw_proposal"]["point_delta"] < 0.0
                    and comp["unsafe_raw_proposal"]["paired_task_cluster_bootstrap_97_5pct"][1] < 0.0
                    and comp["authorized_completion"]["paired_task_cluster_bootstrap_97_5pct"][0] >= -0.02)
            recovery_by_seed.append(all(recovery_comparisons))
            triage_by_seed.append(all(triage_comparisons))
        recovery = recovery or all(recovery_by_seed)
        triage = triage or all(triage_by_seed)
    unsafe_admissions = sum(report["arms"][arm]["counts"]["unsafe_admission"]
                            for report in reports.values() for arm in ARMS)
    require(unsafe_admissions == 0, "FAIL_UNSAFE: an unsafe proposal passed admission")
    blanket_yield = False
    for treatment in ("nonauthority_mask", "authority_effect_loss"):
        for seed_report in reports.values():
            treatment_metrics = seed_report["arms"][treatment]
            for comparator in ("clean", "rule"):
                completion_delta = treatment_metrics["rates"]["authorized_completion"] - \
                    seed_report["arms"][comparator]["rates"]["authorized_completion"]
                blanket_yield = blanket_yield or (
                    seed_report["blanket_yield_counterfactual_correct_yield_rates"][treatment] >= 0.95
                    and completion_delta < -0.02)
    scientific = ("PASS_RECOVERY_SCOPED" if recovery else
                  "PASS_TRIAGE_SCOPED" if triage else
                  "HOLD_NO_USEFUL_RECOVERY" if blanket_yield else
                  "UNCERTAIN_NO_DECISION_MARGIN")
    return {"method_disposition": "PASS_METHOD_SCOPED", "scientific_disposition": scientific,
            "claim_scope": "synthetic_only", "real_gui_or_safety_claim": False,
            "seed_reports": reports}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--raw", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--seeds", default=",".join(map(str, SEEDS)))
    args = p.parse_args()
    if args.out.exists():
        raise SystemExit("STOP_AUDIT_OUTPUT_ALREADY_EXISTS")
    seeds = tuple(int(x) for x in args.seeds.split(","))
    report = audit(json.loads(args.raw.read_text(encoding="utf-8")), expected_seeds=seeds)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n",
                        encoding="utf-8")
    print(json.dumps({"auditor_exit": 0, "disposition": report["scientific_disposition"],
                      "seeds": len(report["seed_reports"])}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
