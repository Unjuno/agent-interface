"""Five-observation ordinary-least-squares looming time-to-contact estimate."""

import math


def estimate_ttc(times, radii):
    """Estimate r/(dr/dt) from all five radius observations and timestamps."""
    if type(times) not in (tuple, list) or type(radii) not in (tuple, list) or len(times) != 5 or len(radii) != 5:
        raise ValueError("five_samples_required")
    if any(type(t) not in (int, float) or not math.isfinite(t) for t in times):
        raise ValueError("finite_numeric_times_required")
    if any(b <= a for a, b in zip(times, times[1:])):
        raise ValueError("strictly_increasing_times")
    if any(type(r) not in (int, float) or not math.isfinite(r) or r <= 0
           for r in radii):
        raise ValueError("finite_positive_radii_required")
    mean_t = sum(times) / len(times)
    mean_r = sum(radii) / len(radii)
    numerator = sum((t - mean_t) * (r - mean_r)
                    for t, r in zip(times, radii))
    denominator = sum((t - mean_t) ** 2 for t in times)
    slope = numerator / denominator
    return radii[-1] / slope if slope > 0 else None
