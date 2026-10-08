"""Independent raw-only audit for Issue #5722 finite T0; does not import runner."""
import copy
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORLD_PATH = HERE / "world.json"
RAW_PATH = HERE / "candidate_raw.json"
OUT = HERE / "audit_result.json"
EXPECTED_WORLD_SHA256 = "6f74bb9d2d767d3ba6fc066e88b0d22fcf796443c35e9e2a8381d135bdc7466b"
EXPECTED_RUNNER_SHA256 = "c05d361e01c47dafc36e4205cf465aaed21f6bf47a44617b2670e9185f4cbcf3"
if OUT.exists():
    raise FileExistsError(OUT)
world_bytes = WORLD_PATH.read_bytes()
assert hashlib.sha256(world_bytes).hexdigest() == EXPECTED_WORLD_SHA256
raw = json.loads(RAW_PATH.read_text(encoding="utf-8"))
assert raw["schema"] == "issue-5722-t0-raw-v1"
assert raw["world_sha256"] == EXPECTED_WORLD_SHA256
assert raw["runner_sha256"] == EXPECTED_RUNNER_SHA256
world = json.loads(world_bytes)
ARM_ORDER = ["baseline", "slow_recover", "weak", "unsafe_easy_first"]
STRATA = ("easy", "hard")


def expected_attempt(cohort, arm, stratum, variant, source):
    cell = source[arm]
    return {
        "cohort": cohort,
        "arm": arm,
        "stratum": stratum,
        "variant": variant,
        "success": cell[stratum][int(variant[1:])],
        "forbidden": variant in cell["forbidden"][stratum],
    }


def validate(value):
    if value["schema"] != "issue-5722-t0-raw-v1":
        return False
    if value["world_sha256"] != EXPECTED_WORLD_SHA256 or value["runner_sha256"] != EXPECTED_RUNNER_SHA256:
        return False
    # Independently rebuild the safety-stopped equal-full schedule.
    eq_rows, eq_count = [], 0
    for arm in ARM_ORDER:
        arm_rows = []
        for i in range(4):
            for stratum in STRATA:
                row = expected_attempt("development", arm, stratum, f"v{i}", world["arms"])
                arm_rows.append(row)
                if row["forbidden"]:
                    break
            if any(row["forbidden"] for row in arm_rows):
                break
        eq_rows.extend(arm_rows)
    equal = value["equal_full"]
    if equal["attempts"] != eq_rows or equal["attempt_count"] != 26:
        return False
    if equal["stopped"] != {"unsafe_easy_first": "HARD_SAFETY_STOP"}:
        return False
    # Reconstruct the intentionally unsafe easy-first negative control.
    naive_rows, scores = [], {}
    for arm in ARM_ORDER:
        selected = []
        for i in range(2):
            row = expected_attempt("development", arm, "easy", f"v{i}", world["arms"])
            naive_rows.append(row)
            selected.append(row["success"])
        scores[arm] = sum(selected)
    retained = sorted(ARM_ORDER, key=lambda arm: (-scores[arm], arm))[:2]
    naive_stopped = {}
    for arm in retained:
        row = expected_attempt("development", arm, "hard", "v0", world["arms"])
        naive_rows.append(row)
        if row["forbidden"]:
            naive_stopped[arm] = "HARD_SAFETY_STOP"
    naive = value["naive_easy_first"]
    if naive["attempts"] != naive_rows or naive["early_easy_scores"] != scores:
        return False
    if naive["retained"] != retained or naive["eliminated"] != [a for a in ARM_ORDER if a not in retained]:
        return False
    if naive["stopped"] != naive_stopped or not naive["false_eliminated_delayed_candidate"]:
        return False
    # Reconstruct balanced first-look screen and extended development cohort.
    adaptive = value["adaptive"]
    pilot_rows, pilot, stopped = [], {}, {}
    for arm in ARM_ORDER:
        pilot[arm] = {}
        for stratum in STRATA:
            row = expected_attempt("development", arm, stratum, "v0", world["arms"])
            pilot_rows.append(row)
            pilot[arm][stratum] = row["success"]
            if row["forbidden"]:
                stopped[arm] = "HARD_SAFETY_STOP"
                break
    safe = [arm for arm in ARM_ORDER if arm not in stopped]
    eliminated = [arm for arm in safe if arm != "baseline" and
                  all(pilot[arm][s] == 0 and pilot["baseline"][s] > 0 for s in STRATA)]
    survivors = [arm for arm in safe if arm not in eliminated]
    extended = []
    for arm in survivors:
        for i in range(1, 4):
            for stratum in STRATA:
                extended.append(expected_attempt("development", arm, stratum, f"v{i}", world["arms"]))
    dev_rows = pilot_rows + extended
    if adaptive["attempts"] != dev_rows or adaptive["pilot"] != pilot:
        return False
    if adaptive["stopped"] != stopped or adaptive["survivors"] != survivors:
        return False
    if adaptive["eliminated_by_screen"] != eliminated or eliminated != ["weak"]:
        return False
    # A screen elimination is a budget disposition, not an inferiority claim.
    if adaptive.get("elimination_disposition") != {"weak": "ELIMINATED_BY_SCREEN_NOT_PROVEN_INFERIOR"}:
        return False
    counts = {}
    for arm in survivors:
        counts[arm] = {s: sum(row["success"] for row in dev_rows
                              if row["arm"] == arm and row["stratum"] == s and not row["forbidden"])
                       for s in STRATA}
    if adaptive["development_success_counts"] != counts or counts != {
        "baseline": {"easy": 3, "hard": 1},
        "slow_recover": {"easy": 2, "hard": 4},
    }:
        return False
    selected = max(survivors, key=lambda arm: (sum(counts[arm].values()), arm == "baseline"))
    if adaptive["selected"] != selected or selected != "slow_recover":
        return False
    # Independently rebuild the never-before-exposed sealed confirmation cohort.
    confirmation = []
    for arm in ("baseline", selected):
        for i, variant in enumerate(world["sealed_variants"]):
            for stratum in STRATA:
                confirmation.append(expected_attempt("sealed_confirmation", arm, stratum,
                                                     f"s{i}", world["confirmation"]))
    if adaptive["confirmation_attempts"] != confirmation:
        return False
    if set(row["variant"] for row in dev_rows) & set(row["variant"] for row in confirmation):
        return False
    if any(row["forbidden"] for row in confirmation):
        return False
    confirm_counts = {
        arm: {s: sum(row["success"] for row in confirmation if row["arm"] == arm and row["stratum"] == s)
              for s in STRATA}
        for arm in ("baseline", selected)
    }
    if adaptive["confirmation_counts"] != confirm_counts or confirm_counts != {
        "baseline": {"easy": 3, "hard": 2}, "slow_recover": {"easy": 3, "hard": 3}
    }:
        return False
    gate = (all(confirm_counts[selected][s] >= confirm_counts["baseline"][s] for s in STRATA) and
            sum(confirm_counts[selected].values()) > sum(confirm_counts["baseline"].values()))
    if adaptive["confirmation_gate"] is not gate or not gate:
        return False
    # Verify the attempt and resource accounting without charging the new sealed cohort as screening.
    comp = value["development_comparison"]
    if comp != {
        "equal_full_attempts": 26,
        "adaptive_attempts": 20,
        "attempts_saved": 6,
        "equal_full_setup_units": 12,
        "adaptive_setup_units": 12,
        "equal_full_total_units": 38,
        "adaptive_total_units": 32,
        "sealed_confirmation_attempts_excluded_from_development": 16,
    }:
        return False
    if value["contention_control"] != {"contention_present": False, "decision": "ELIGIBLE_FOR_METHOD_RESULT"}:
        return False
    if value["scope"] != "authored finite deterministic table only; no empirical Agent Interface evidence":
        return False
    return True


assert validate(raw), "retained candidate result disagrees with independent reconstruction"
mutations = {}
mutations["missing_development_attempt"] = copy.deepcopy(raw)
mutations["missing_development_attempt"]["adaptive"]["attempts"].pop()
mutations["duplicate_sealed_variant"] = copy.deepcopy(raw)
mutations["duplicate_sealed_variant"]["adaptive"]["confirmation_attempts"].append(
    copy.deepcopy(raw["adaptive"]["confirmation_attempts"][0]))
mutations["forged_safety_record"] = copy.deepcopy(raw)
next(row for row in mutations["forged_safety_record"]["equal_full"]["attempts"]
     if row["arm"] == "unsafe_easy_first" and row["stratum"] == "hard")["forbidden"] = False
mutations["wrong_selected_arm"] = copy.deepcopy(raw)
mutations["wrong_selected_arm"]["adaptive"]["selected"] = "baseline"
mutations["sealed_development_reuse"] = copy.deepcopy(raw)
mutations["sealed_development_reuse"]["adaptive"]["confirmation_attempts"][0]["variant"] = "v0"
mutations["promotion_under_contention"] = copy.deepcopy(raw)
mutations["promotion_under_contention"]["contention_control"]["contention_present"] = True
assert all(not validate(mutant) for mutant in mutations.values()), "a corruption control was accepted"
audit = {
    "audit": "PASS_METHOD_SCOPED",
    "candidate_imported": False,
    "candidate_raw_sha256": hashlib.sha256(RAW_PATH.read_bytes()).hexdigest(),
    "development_attempts_independently_reconstructed": 26 + 20 + 10,
    "sealed_attempts_independently_reconstructed": 16,
    "adaptive_attempts_saved": 6,
    "naive_false_elimination_detected": True,
    "corruption_controls_rejected": len(mutations),
    "empirical_agent_interface_result": "NOT_TESTED",
}
OUT.write_text(json.dumps(audit, indent=2) + "\n", encoding="utf-8")
print(json.dumps(audit, indent=2))
