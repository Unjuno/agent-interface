import itertools
import json
from dataclasses import dataclass


@dataclass(frozen=True)
class DwellObservation:
    duration: float
    completed: bool
    horizon: float


def identify_mean_interval(observations: list[DwellObservation], upper_bound: float) -> tuple[float, float]:
    if not observations:
        raise ValueError("empty_population")
    if upper_bound < 0:
        raise ValueError("negative_upper_bound")
    lower = 0.0
    upper = 0.0
    for obs in observations:
        if obs.horizon < 0 or obs.horizon > upper_bound:
            raise ValueError("invalid_horizon")
        if obs.completed:
            if obs.duration < 0 or obs.duration > upper_bound:
                raise ValueError("invalid_completed_duration")
            lower += obs.duration
            upper += obs.duration
        else:
            if obs.duration != obs.horizon:
                raise ValueError("censored_duration_must_equal_horizon")
            lower += obs.horizon
            upper += upper_bound
    n = len(observations)
    return lower / n, upper / n


def finite_grid_check(observations: list[DwellObservation], upper_bound: float, step: float = 1.0) -> bool:
    lo, hi = identify_mean_interval(observations, upper_bound)
    censored = [o for o in observations if not o.completed]
    choices = [tuple(x * step for x in range(int(o.horizon / step), int(upper_bound / step) + 1)) for o in censored]
    for values in itertools.product(*choices):
        i = iter(values)
        total = 0.0
        for obs in observations:
            total += obs.duration if obs.completed else next(i)
        mean = total / len(observations)
        if not (lo <= mean <= hi):
            return False
    return True


def run():
    observations = [
        DwellObservation(2.0, True, 2.0),
        DwellObservation(5.0, False, 5.0),
        DwellObservation(7.0, True, 7.0),
    ]
    lo, hi = identify_mean_interval(observations, 10.0)
    assert (lo, hi) == (14.0 / 3.0, 19.0 / 3.0)
    assert finite_grid_check(observations, 10.0)
    assert observations[1].completed is False
    try:
        identify_mean_interval([DwellObservation(6.0, False, 5.0)], 10.0)
    except ValueError as exc:
        assert str(exc) == "censored_duration_must_equal_horizon"
    else:
        raise AssertionError("malformed censor accepted")
    return {
        "status": "PASS_DWELL_TIMEOUT_ORACLE_SCOPED",
        "cases": 4,
        "interval": [lo, hi],
        "censored_not_completion": True,
        "finite_grid_coverage": True,
        "live_gui_calls": 0,
        "model_calls": 0,
        "network_calls": 0,
    }


if __name__ == "__main__":
    print(json.dumps(run(), sort_keys=True))
