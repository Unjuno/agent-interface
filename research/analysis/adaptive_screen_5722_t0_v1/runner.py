"""One-shot finite T0 candidate for Issue #5722; authored table only."""
import hashlib
import json
import platform
from pathlib import Path


HERE = Path(__file__).resolve().parent
WORLD_PATH = HERE / "world.json"
OUT = HERE / "candidate_raw.json"
if OUT.exists():
    raise FileExistsError(OUT)
world_bytes = WORLD_PATH.read_bytes()
world = json.loads(world_bytes)
arms = list(world["arms"])


def attempt(cohort, arm, stratum, variant, source):
    row = source[arm]
    return {
        "cohort": cohort,
        "arm": arm,
        "stratum": stratum,
        "variant": variant,
        "success": row[stratum][int(variant[1:])],
        "forbidden": variant in row["forbidden"][stratum],
    }


def run_equal_full():
    rows = []
    stopped = {}
    for arm in arms:
        for i in range(4):
            for stratum in ("easy", "hard"):
                item = attempt("development", arm, stratum, f"v{i}", world["arms"])
                rows.append(item)
                if item["forbidden"]:
                    stopped[arm] = "HARD_SAFETY_STOP"
                    break
            if arm in stopped:
                break
    return {"attempts": rows, "stopped": stopped, "attempt_count": len(rows)}


def run_naive_easy_first():
    rows = []
    scores = {}
    for arm in arms:
        selected = []
        for i in range(2):
            item = attempt("development", arm, "easy", f"v{i}", world["arms"])
            rows.append(item)
            selected.append(item["success"])
        scores[arm] = sum(selected)
    retained = sorted(arms, key=lambda arm: (-scores[arm], arm))[:2]
    stopped = {}
    for arm in retained:
        item = attempt("development", arm, "hard", "v0", world["arms"])
        rows.append(item)
        if item["forbidden"]:
            stopped[arm] = "HARD_SAFETY_STOP"
    eliminated = [arm for arm in arms if arm not in retained]
    return {
        "attempts": rows,
        "early_easy_scores": scores,
        "retained": retained,
        "eliminated": eliminated,
        "stopped": stopped,
        "false_eliminated_delayed_candidate": "slow_recover" in eliminated,
    }


def run_adaptive():
    rows = []
    stopped = {}
    pilot = {}
    for arm in arms:
        pilot[arm] = {}
        for stratum in ("easy", "hard"):
            item = attempt("development", arm, stratum, "v0", world["arms"])
            rows.append(item)
            pilot[arm][stratum] = item["success"]
            if item["forbidden"]:
                stopped[arm] = "HARD_SAFETY_STOP"
                break
        if arm in stopped:
            continue
    safe = [arm for arm in arms if arm not in stopped]
    baseline = "baseline"
    eliminated_by_screen = []
    for arm in safe:
        if arm != baseline and all(pilot[arm][s] == 0 and pilot[baseline][s] > 0
                                   for s in ("easy", "hard")):
            eliminated_by_screen.append(arm)
    survivors = [arm for arm in safe if arm not in eliminated_by_screen]
    for arm in survivors:
        for i in range(1, 4):
            for stratum in ("easy", "hard"):
                rows.append(attempt("development", arm, stratum, f"v{i}", world["arms"]))
    counts = {
        arm: {
            s: sum(row["success"] for row in rows
                   if row["cohort"] == "development" and row["arm"] == arm and
                   row["stratum"] == s and not row["forbidden"])
            for s in ("easy", "hard")
        }
        for arm in survivors
    }
    selected = max(survivors, key=lambda arm: (sum(counts[arm].values()), arm == baseline))
    # The sealed comparison is a separate matched cohort and does not consume
    # development-screening budget.
    confirm = []
    for arm in (baseline, selected):
        for i, variant in enumerate(world["sealed_variants"]):
            for stratum in ("easy", "hard"):
                confirm.append(attempt("sealed_confirmation", arm, stratum,
                                       f"s{i}", world["confirmation"]))
    confirmation_counts = {
        arm: {s: sum(row["success"] for row in confirm
                     if row["arm"] == arm and row["stratum"] == s)
              for s in ("easy", "hard")}
        for arm in (baseline, selected)
    }
    gate = (not any(row["forbidden"] for row in confirm) and
            all(confirmation_counts[selected][s] >= confirmation_counts[baseline][s]
                for s in ("easy", "hard")) and
            sum(confirmation_counts[selected].values()) >
            sum(confirmation_counts[baseline].values()))
    return {
        "attempts": rows,
        "pilot": pilot,
        "stopped": stopped,
        "eliminated_by_screen": eliminated_by_screen,
        "elimination_disposition": {
            arm: "ELIMINATED_BY_SCREEN_NOT_PROVEN_INFERIOR"
            for arm in eliminated_by_screen
        },
        "survivors": survivors,
        "development_success_counts": counts,
        "selected": selected,
        "development_attempt_count": len(rows),
        "confirmation_attempts": confirm,
        "confirmation_counts": confirmation_counts,
        "confirmation_gate": gate,
    }


equal = run_equal_full()
naive = run_naive_easy_first()
adaptive = run_adaptive()
setup_units = world["setup_units_per_arm"] * len(arms)
full_dev = equal["attempt_count"]
adaptive_dev = adaptive["development_attempt_count"]
raw = {
    "schema": "issue-5722-t0-raw-v1",
    "world_sha256": hashlib.sha256(world_bytes).hexdigest(),
    "runner_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    "runtime": platform.python_version(),
    "equal_full": equal,
    "naive_easy_first": naive,
    "adaptive": adaptive,
    "development_comparison": {
        "equal_full_attempts": full_dev,
        "adaptive_attempts": adaptive_dev,
        "attempts_saved": full_dev - adaptive_dev,
        "equal_full_setup_units": setup_units,
        "adaptive_setup_units": setup_units,
        "equal_full_total_units": full_dev + setup_units,
        "adaptive_total_units": adaptive_dev + setup_units,
        "sealed_confirmation_attempts_excluded_from_development":
            len(adaptive["confirmation_attempts"]),
    },
    "contention_control": {"contention_present": False, "decision": "ELIGIBLE_FOR_METHOD_RESULT"},
    "scope": "authored finite deterministic table only; no empirical Agent Interface evidence",
}
OUT.write_text(json.dumps(raw, indent=2) + "\n", encoding="utf-8")
print(json.dumps({
    "equal_full_development_attempts": full_dev,
    "adaptive_development_attempts": adaptive_dev,
    "attempts_saved": full_dev - adaptive_dev,
    "equal_full_total_resource_units": full_dev + setup_units,
    "adaptive_total_resource_units": adaptive_dev + setup_units,
    "naive_false_eliminated_delayed_candidate": naive["false_eliminated_delayed_candidate"],
    "adaptive_selected": adaptive["selected"],
    "sealed_confirmation_gate": adaptive["confirmation_gate"],
    "scope": raw["scope"],
}, indent=2))
