"""Pure-standard-library ordinal power sensitivity model for #8032 T0 A02."""

import bisect
import hashlib
import math
import struct


def _validate_distribution(probabilities):
    if len(probabilities) != 5 or any(p < 0 or p > 1 for p in probabilities):
        raise ValueError("expected five probabilities in [0, 1]")
    if not math.isclose(sum(probabilities), 1.0, abs_tol=1e-12):
        raise ValueError("probabilities must sum to one")


def shift_distribution(probabilities, odds_ratio):
    """Apply a common cumulative-odds shift toward higher ordered categories."""
    _validate_distribution(probabilities)
    if not math.isfinite(odds_ratio) or odds_ratio <= 0:
        raise ValueError("odds_ratio must be finite and positive")
    survivals = [sum(probabilities[k:]) for k in range(1, len(probabilities))]
    shifted_survivals = []
    for p in survivals:
        if p <= 0:
            shifted_survivals.append(0.0)
        elif p >= 1:
            shifted_survivals.append(1.0)
        else:
            odds = p / (1.0 - p) * odds_ratio
            shifted_survivals.append(odds / (1.0 + odds))
    result = [1.0 - shifted_survivals[0]]
    result.extend(shifted_survivals[i - 1] - shifted_survivals[i]
                  for i in range(1, len(shifted_survivals)))
    result.append(shifted_survivals[-1])
    if any(p < -1e-12 for p in result):
        raise ValueError("invalid proportional-odds distribution")
    result = [max(0.0, p) for p in result]
    total = sum(result)
    return [p / total for p in result]


def _mean_variance(probabilities):
    scores = [i / 4 for i in range(5)]
    mean = sum(p * x for p, x in zip(probabilities, scores))
    variance = sum(p * (x - mean) ** 2 for p, x in zip(probabilities, scores))
    return mean, variance


def _standardized_difference(left, right):
    m0, v0 = _mean_variance(left)
    m1, v1 = _mean_variance(right)
    pooled_sd = math.sqrt((v0 + v1) / 2)
    if pooled_sd == 0:
        return 0.0
    return (m1 - m0) / pooled_sd


def calibrate_effect(baseline, target_d):
    """Solve a proportional-odds shift whose score-scale pooled-SD d matches target."""
    _validate_distribution(baseline)
    if not math.isfinite(target_d) or target_d <= 0:
        raise ValueError("target_d must be finite and positive")
    lo, hi = 1.0, 1e8
    if _standardized_difference(baseline, shift_distribution(baseline, hi)) < target_d:
        raise ValueError("target d is beyond this baseline's ceiling")
    for _ in range(80):
        mid = (lo + hi) / 2
        shifted = shift_distribution(baseline, mid)
        if _standardized_difference(baseline, shifted) < target_d:
            lo = mid
        else:
            hi = mid
    odds_ratio = (lo + hi) / 2
    shifted = shift_distribution(baseline, odds_ratio)
    return odds_ratio, shifted, _standardized_difference(baseline, shifted)


def rank_sum_u(left_counts, right_counts):
    """Count left-vs-right ordinal wins with half credit for ties."""
    if len(left_counts) != 5 or len(right_counts) != 5:
        raise ValueError("expected five ordinal categories")
    below = 0
    score = 0.0
    for left, right in zip(left_counts, right_counts):
        score += left * (below + right / 2)
        below += right
    return score


class _SplitMix64:
    def __init__(self, seed):
        self.state = seed & 0xFFFFFFFFFFFFFFFF

    def uniform(self):
        self.state = (self.state + 0x9E3779B97F4A7C15) & 0xFFFFFFFFFFFFFFFF
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & 0xFFFFFFFFFFFFFFFF
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & 0xFFFFFFFFFFFFFFFF
        z ^= z >> 31
        return (z >> 11) / 9007199254740992.0


def _draw_counts(rng, cumulative, n):
    counts = [0] * 5
    for _ in range(n):
        counts[bisect.bisect_left(cumulative, rng.uniform())] += 1
    return counts


def _tie_corrected_variance(left_counts, right_counts):
    n_left = sum(left_counts)
    n_right = sum(right_counts)
    total = n_left + n_right
    correction = sum((a + b) ** 3 - (a + b) for a, b in zip(left_counts, right_counts))
    return n_left * n_right / 12 * (total + 1 - correction / (total * (total - 1)))


def simulate_rank_power(left, right, n, reps, seed, alpha=0.0125):
    """Estimate two-sided tie-corrected normal-approximation rank-sum power."""
    _validate_distribution(left)
    _validate_distribution(right)
    if n < 2 or reps < 100 or not (0 < alpha < 1):
        raise ValueError("invalid simulation size or alpha")
    left_cumulative = []
    right_cumulative = []
    running = 0.0
    for p in left:
        running += p
        left_cumulative.append(running)
    running = 0.0
    for p in right:
        running += p
        right_cumulative.append(running)
    rng = _SplitMix64(seed)
    digest = hashlib.sha256()
    critical = 2.498  # frozen conservative normal cutoff for two-sided alpha=.0125
    rejected = 0
    for _ in range(reps):
        left_counts = _draw_counts(rng, left_cumulative, n)
        right_counts = _draw_counts(rng, right_cumulative, n)
        u = rank_sum_u(left_counts, right_counts)
        variance = _tie_corrected_variance(left_counts, right_counts)
        z = (u - n * n / 2) / math.sqrt(variance) if variance else 0.0
        if abs(z) >= critical:
            rejected += 1
        digest.update(struct.pack("<5Q", *(a + b for a, b in zip(left_counts, right_counts))))
    power = rejected / reps
    return {
        "n_per_arm": n,
        "replicates": reps,
        "rejections": rejected,
        "power": power,
        "mcse": math.sqrt(power * (1 - power) / reps),
        "alpha": alpha,
        "critical_abs_z": critical,
        "pooled_category_counts_sha256": digest.hexdigest(),
    }
