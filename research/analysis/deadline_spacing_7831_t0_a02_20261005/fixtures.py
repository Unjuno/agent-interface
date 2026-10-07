"""Frozen finite trajectories and sensitivity grid shared as raw inputs."""


def traces():
    return {
        "noisy_oscillation": {
            "margin": [20] * 10,
            "signal": [5, 0, 5, 0, 5, 0, 5, 0, 5, 5],
            "horizon": 9, "missing": [], "hard": [], "budget": 99},
        "transient_burst": {
            "margin": [20] * 10,
            "signal": [5, 0, 0, 0, 0, 0, 5, 5, 5, 5],
            "horizon": 9, "missing": [], "hard": [], "budget": 99},
        "sustained_approach": {
            "margin": [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
            "signal": [12, 11, 10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
            "horizon": 12, "missing": [], "hard": [], "budget": 99},
        "hard_invalidation": {
            "margin": [30] * 11, "signal": [5] * 11,
            "horizon": 10, "missing": [], "hard": [2], "budget": 99},
        "missing_due_measurement": {
            "margin": [20] * 41, "signal": [5] * 41,
            "horizon": 40, "missing": list(range(1, 41)),
            "hard": [], "budget": 99},
        "delayed_due_measurement": {
            "margin": [20] * 41, "signal": [5] * 41,
            "horizon": 40, "missing": [], "delayed": list(range(1, 41)),
            "hard": [], "budget": 99},
        "spacing_conflict": {
            "margin": [10, 9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
            "signal": [5] * 11, "horizon": 10,
            "missing": [], "hard": [], "budget": 99},
        "budget_exhausted": {
            "margin": [30] * 61, "signal": [5] * 61,
            "horizon": 60, "missing": [], "hard": [], "budget": 1},
    }


def sensitivity_grid():
    for decline in (1, 2):
        for growth in (0, 1):
            for latency in (1, 2):
                for spacing in (2, 3):
                    yield {"decline_bound": decline,
                           "uncertainty_growth": growth,
                           "latency": latency,
                           "minimum_spacing": spacing,
                           "fixed_period": 3}
