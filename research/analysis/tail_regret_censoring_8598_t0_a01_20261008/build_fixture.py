"""Build deterministic paired censoring cohorts before the formal freeze."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


ARMS = (
    "independent_admin",
    "recorded_covariate",
    "latent_tail_informative",
    "zero_positivity",
    "near_zero_positivity",
    "no_censoring",
)
STRATA = ("s0", "s1")
ROUTES = ("A", "B")
HORIZON = 4
MAX_PER_TICK = 3
ALPHA = 0.75
MINIMUM_PROPENSITY = 0.05
PAIRS_PER_STRATUM = 8
PAIR_BANK_SIZE = 12


def _digest_int(text: str, width: int = 8) -> int:
    return int.from_bytes(hashlib.sha256(text.encode("utf-8")).digest()[:width], "big")


def _trajectory(route: str, pair_id: int) -> list[int]:
    if route == "A" and pair_id < 4:
        return [0, 0, 3, 3]  # 4/12 opportunities have loss 6; population mean 2, CVaR .75 = 6.
    if route == "B" and pair_id < 8:
        return [0, 0, 1, 2]  # 8/12 opportunities have loss 3; population mean 2, CVaR .75 = 3.
    return [0, 0, 0, 0]


def _covariate(pair_id: int) -> str:
    return "complex" if pair_id < 8 else "simple"


def _probabilities(arm: str, covariate: str, route: str, loss: int) -> tuple[float, float]:
    """Return (actual resolution probability, candidate-declared model probability)."""
    if arm == "independent_admin":
        return 0.70, 0.70
    if arm == "recorded_covariate":
        probability = 0.40 if covariate == "complex" else 0.90
        return probability, probability
    if arm == "latent_tail_informative":
        actual = 0.05 if loss > 0 else 0.90
        return actual, 0.70  # deliberately withheld model; this arm is non-identifying
    if arm == "zero_positivity":
        probability = 0.0 if covariate == "complex" else 0.90
        return probability, probability
    if arm == "near_zero_positivity":
        probability = 0.02 if covariate == "complex" else 0.90
        return probability, probability
    if arm == "no_censoring":
        return 1.0, 1.0
    raise ValueError(f"unknown censoring arm: {arm}")


def build_fixture(repetitions: int = 128) -> tuple[dict[str, Any], dict[str, Any]]:
    if type(repetitions) is not int or not 1 <= repetitions <= 128:
        raise ValueError("repetitions must be an integer from 1 through the frozen maximum 128")
    public: dict[str, Any] = {
        "schema": "8598-observed-v1",
        "settings": {
            "horizon": HORIZON,
            "max_regret_per_tick": MAX_PER_TICK,
            "cvar_alpha": ALPHA,
            "minimum_completion_propensity": MINIMUM_PROPENSITY,
            "routes": list(ROUTES),
            "strata": list(STRATA),
            "repetitions": repetitions,
            "pairs_per_stratum_per_cohort": PAIRS_PER_STRATUM,
            "pair_bank_size_per_stratum": PAIR_BANK_SIZE,
            "primary_tail_estimand": "equal-stratum-macro-average-of-route-level-opportunity-CVaR",
            "upper_tail_mass": 1.0 - ALPHA,
            "effective_sample_size": "(sum weights)^2 / sum squared weights, per route-stratum",
            "minimum_supported_completion_probability": MINIMUM_PROPENSITY,
        },
        "cohorts": [],
        "categorical_controls": [
            {"control_id": "hard-safety-control-01", "kind": "hard_safety", "state": "FAIL_HARD_SAFETY"},
            {"control_id": "missing-truth-control-01", "kind": "missing_truth", "state": "UNKNOWN"},
        ],
    }
    truth: dict[str, Any] = {"schema": "8598-truth-v1", "opportunities": [], "categorical_controls": [
        {"control_id": "hard-safety-control-01", "kind": "hard_safety", "state": "FAIL_HARD_SAFETY"},
        {"control_id": "missing-truth-control-01", "kind": "missing_truth", "state": "UNKNOWN"},
    ]}

    for arm in ARMS:
        for seed in range(repetitions):
            cohort = {"seed": seed, "arm": arm, "opportunities": []}
            for stratum in STRATA:
                selected = sorted(
                    range(PAIR_BANK_SIZE),
                    key=lambda pair: hashlib.sha256(f"sample:{seed}:{stratum}:{pair}".encode("utf-8")).digest(),
                )[:PAIRS_PER_STRATUM]
                for pair_id in selected:
                    covariate = _covariate(pair_id)
                    for route in ROUTES:
                        increments = _trajectory(route, pair_id)
                        loss = sum(increments)
                        actual_p, model_p = _probabilities(arm, covariate, route, loss)
                        uniform = _digest_int(f"completion:{seed}:{arm}:{stratum}:{pair_id}") / 2**64
                        resolved = uniform < actual_p
                        if resolved:
                            ticks = HORIZON
                        else:
                            ticks = 1 + _digest_int(f"followup:{seed}:{arm}:{stratum}:{pair_id}:{route}", 4) % (HORIZON - 1)
                        identifier = f"{arm}-s{seed:03d}-{stratum}-p{pair_id:02d}-{route}"
                        observed = increments[:ticks]
                        row: dict[str, Any] = {
                            "opportunity_id": identifier,
                            "route": route,
                            "stratum": stratum,
                            "pair_id": pair_id,
                            "covariate": covariate,
                            "resolved": resolved,
                            "followup_ticks": ticks,
                            "observed_increments": observed,
                            "p_resolve_model": model_p,
                        }
                        if resolved:
                            row["terminal_loss"] = loss
                        cohort["opportunities"].append(row)
                        truth["opportunities"].append({
                            "opportunity_id": identifier,
                            "seed": seed,
                            "arm": arm,
                            "route": route,
                            "stratum": stratum,
                            "pair_id": pair_id,
                            "covariate": covariate,
                            "increments": increments,
                            "terminal_loss": loss,
                            "actual_completion_probability": actual_p,
                        })
            public["cohorts"].append(cohort)
    return public, truth


def write_fixture(directory: Path, repetitions: int = 128) -> None:
    public, truth = build_fixture(repetitions)
    directory.mkdir(parents=True, exist_ok=True)
    for name, value in (("public_input.json", public), ("truth.json", truth)):
        payload = json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
        with (directory / name).open("xb") as stream:
            stream.write(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--repetitions", type=int, default=128)
    args = parser.parse_args(argv)
    write_fixture(args.directory, args.repetitions)
    public, _ = build_fixture(args.repetitions)
    print(f"CONSTRUCTION_FIXTURE_READY cohorts={len(public['cohorts'])} opportunities={sum(len(c['opportunities']) for c in public['cohorts'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
