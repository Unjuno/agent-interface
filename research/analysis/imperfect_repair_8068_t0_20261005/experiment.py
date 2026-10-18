"""Finite, authored recovery-effectiveness fixture for Issue #8068 T0."""
from dataclasses import dataclass


@dataclass(frozen=True)
class Cycle:
    cycle_id: str
    fault_class: str
    pre_age: int
    exposure: int
    repair: str
    observed_post_age: int
    required_effects: tuple[str, ...]
    retained_effects: tuple[str, ...]
    recurrence_u: float | None
    recurrence_exposure: int | None
    observed_recurrence: bool | None
    censored: bool = False


def latent_post_age(pre_age: int, repair: str) -> int:
    if repair == "perfect":
        return 0
    if repair == "minimal":
        return pre_age
    if repair == "imperfect":
        return max(0, pre_age - 1)
    raise ValueError("unknown repair scope")


def recurrence_probability(age: int) -> float:
    return 0.1 + 0.2 * age


def frozen_cycles() -> tuple[Cycle, ...]:
    # IDs, classes, exposure, operator, required effects and censoring are frozen
    # independently of candidate-reported outcomes in the auditor manifest.
    specs = (
        ("p0", "worker_fault", 0, 1, "perfect", ("save-01",), 0.05, 1, False),
        ("p1", "worker_fault", 2, 2, "perfect", ("save-02",), 0.25, 2, False),
        ("m0", "worker_fault", 0, 1, "minimal", ("save-03",), 0.05, 1, False),
        ("m1", "worker_fault", 2, 2, "minimal", ("save-04",), 0.55, 2, False),
        ("i0", "worker_fault", 0, 1, "imperfect", ("save-05",), 0.05, 1, False),
        ("i1", "worker_fault", 2, 2, "imperfect", ("save-06",), 0.25, 2, False),
        ("c0", "worker_fault", 2, 3, "imperfect", ("save-07",), None, None, True),
    )
    rows = []
    for cid, fault, age, exposure, repair, effects, u, followup, censored in specs:
        post = latent_post_age(age, repair)
        recurrence = None if censored else u < recurrence_probability(post)
        rows.append(Cycle(cid, fault, age, exposure, repair, post, effects,
                          effects, u, followup, recurrence, censored))
    return tuple(rows)


def summarize(cycles: tuple[Cycle, ...]) -> dict:
    return {
        "repair_post_ages": {r.cycle_id: latent_post_age(r.pre_age, r.repair)
                             for r in cycles},
        "observed_post_ages": {r.cycle_id: r.observed_post_age for r in cycles},
        "recurrence_observed": {r.cycle_id: r.observed_recurrence for r in cycles},
        "censored": sorted(r.cycle_id for r in cycles if r.censored),
        "exposure_total": sum(r.exposure for r in cycles),
    }


if __name__ == "__main__":
    import json
    print(json.dumps(summarize(frozen_cycles()), sort_keys=True))
