"""Upper-tail TailID algorithmic equivalent for the #6576 CPU fixture.

Source basis: TailID 1.0.0, tag commit
f99b10ff27f37ac62ba1d44ce79b4fc886f72997; Manau et al., ECRTS 2025,
https://doi.org/10.4230/LIPIcs.ECRTS.2025.20. The GPD MLE initialization and
likelihood follow ismev 1.43's gpd.fit implementation (source repository
commit 25223b17285d45bf3911efd79ac75f363e7ae495). This is a Python
reimplementation, not the CRAN R package; numerical optimizer equivalence
must be verified before it is used as a formal comparator.
"""

from __future__ import annotations

import math
from statistics import NormalDist


def quantile_type7(sample: list[float], probability: float) -> float:
    ordered = sorted(sample)
    if not ordered or not 0 <= probability <= 1:
        raise ValueError("invalid quantile input")
    h = (len(ordered) - 1) * probability
    lower = math.floor(h)
    fraction = h - lower
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + fraction * (ordered[upper] - ordered[lower])


def _nll(excesses: list[float], log_scale: float, shape: float) -> float:
    scale = math.exp(log_scale)
    if not math.isfinite(scale) or scale <= 0:
        return 1e100
    total = len(excesses) * log_scale
    if abs(shape) < 1e-7:
        return total + sum(excesses) / scale
    for value in excesses:
        support = 1 + shape * value / scale
        if support <= 0 or not math.isfinite(support):
            return 1e100
        total += (1 + 1 / shape) * math.log(support)
    return total


def fit_gpd_parameters(excesses: list[float], max_iter: int = 3000) -> tuple[float, float]:
    """Return (scale, shape) from a deterministic two-parameter GPD MLE."""
    if len(excesses) < 3 or any(v < 0 or not math.isfinite(v) for v in excesses):
        raise ValueError("insufficient or invalid exceedances")
    mean = sum(excesses) / len(excesses)
    variance = sum((v - mean) ** 2 for v in excesses) / (len(excesses) - 1)
    scale0 = math.sqrt(6 * variance) / math.pi
    if scale0 <= 0 or not math.isfinite(scale0):
        raise ValueError("degenerate exceedances")
    start = (math.log(scale0), 0.1)
    simplex = [start, (start[0] + 0.05, start[1]), (start[0], start[1] + 0.05)]
    objective = lambda point: _nll(excesses, point[0], point[1])
    values = [objective(point) for point in simplex]

    for _ in range(max_iter):
        order = sorted(range(3), key=lambda i: values[i])
        simplex = [simplex[i] for i in order]
        values = [values[i] for i in order]
        spread = max(abs(values[i] - values[0]) for i in (1, 2))
        diameter = max(
            math.dist(simplex[0], simplex[i]) for i in (1, 2)
        )
        if spread < 1e-9 and diameter < 1e-7:
            break

        best, second, worst = simplex
        centroid = ((best[0] + second[0]) / 2, (best[1] + second[1]) / 2)
        reflected = (centroid[0] + (centroid[0] - worst[0]), centroid[1] + (centroid[1] - worst[1]))
        reflected_value = objective(reflected)

        if values[0] <= reflected_value < values[1]:
            simplex[2], values[2] = reflected, reflected_value
            continue
        if reflected_value < values[0]:
            expanded = (centroid[0] + 2 * (reflected[0] - centroid[0]), centroid[1] + 2 * (reflected[1] - centroid[1]))
            expanded_value = objective(expanded)
            if expanded_value < reflected_value:
                simplex[2], values[2] = expanded, expanded_value
            else:
                simplex[2], values[2] = reflected, reflected_value
            continue

        contracted = (
            centroid[0] + 0.5 * (worst[0] - centroid[0]),
            centroid[1] + 0.5 * (worst[1] - centroid[1]),
        )
        contracted_value = objective(contracted)
        if contracted_value < values[2]:
            simplex[2], values[2] = contracted, contracted_value
            continue

        simplex = [best, ((best[0] + second[0]) / 2, (best[1] + second[1]) / 2), ((best[0] + worst[0]) / 2, (best[1] + worst[1]) / 2)]
        values = [objective(point) for point in simplex]

    best_index = min(range(3), key=lambda i: values[i])
    if values[best_index] >= 1e99:
        raise ValueError("GPD MLE did not find a supported solution")
    log_scale, shape = simplex[best_index]
    return math.exp(log_scale), shape


def fit_gpd_shape(excesses: list[float], max_iter: int = 3000) -> float:
    """Compatibility wrapper returning only the fitted GPD shape."""
    return fit_gpd_parameters(excesses, max_iter=max_iter)[1]


def shape_interval(shape: float, exceedance_count: int, confidence: float) -> tuple[float, float]:
    if exceedance_count < 1 or not 0 < confidence < 1:
        raise ValueError("invalid confidence-interval input")
    z = NormalDist().inv_cdf((1 + confidence) / 2)
    radius = z * abs(shape) / math.sqrt(exceedance_count)
    return shape - radius, shape + radius


def tailid_sensitive_upper(
    sample: list[float],
    threshold_probability: float = 0.90,
    confidence: float = 0.9999,
    candidate_fraction_of_tail: float = 0.05,
) -> dict:
    """Return TailID-sensitive upper-tail points and threshold metadata.

    The candidate count follows p_c1 = 1 - candidate_fraction_of_tail *
    (1 - p_M). Candidates are reintroduced from least to most extreme. On
    the first shape estimate above the previous CI, that and every larger
    candidate is marked sensitive, matching TailID's stopping rule.
    """
    if len(sample) < 100 or not 0 < threshold_probability < 1:
        raise ValueError("sample/threshold outside frozen TailID fixture bounds")
    threshold = quantile_type7(sample, threshold_probability)
    count_float = candidate_fraction_of_tail * (1 - threshold_probability) * len(sample)
    candidate_count = round(count_float)
    if abs(count_float - candidate_count) > 1e-9:
        raise ValueError("candidate count must be integral under the frozen fixture")
    if candidate_count < 1:
        return {"threshold": threshold, "sensitive": [], "reference_shape": None}
    # Index-based removal preserves duplicate values correctly.
    ranked_indices = sorted(range(len(sample)), key=lambda i: sample[i], reverse=True)[:candidate_count]
    removed = set(ranked_indices)
    base = [value for i, value in enumerate(sample) if i not in removed]
    base_excesses = [value - threshold for value in base if value > threshold]
    shape = fit_gpd_shape(base_excesses)
    interval = shape_interval(shape, len(base_excesses), confidence)

    sensitive: list[float] = []
    ordered_candidates = list(reversed(ranked_indices))
    for position, index in enumerate(ordered_candidates):
        restored = base + [sample[index]]
        excesses = [value - threshold for value in restored if value > threshold]
        updated_shape = fit_gpd_shape(excesses)
        if updated_shape > interval[1]:
            remaining = [sample[i] for i in ordered_candidates[position:]]
            sensitive = sorted(remaining, reverse=True)
            break
        shape = updated_shape
        interval = shape_interval(shape, len(excesses), confidence)

    return {
        "threshold": threshold,
        "sensitive": sensitive,
        "reference_shape": shape,
        "candidate_count": candidate_count,
    }
