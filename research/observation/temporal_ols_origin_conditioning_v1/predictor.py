def _ols_predict(times_s, positions, target_s):
    if len(times_s) != len(positions) or len(times_s) < 2:
        raise ValueError('bad_samples')
    mt = sum(times_s) / len(times_s)
    mx = sum(positions) / len(positions)
    den = sum((t-mt)*(t-mt) for t in times_s)
    if den <= 0.0:
        raise ValueError('degenerate_time')
    slope = sum((t-mt)*(x-mx) for t,x in zip(times_s, positions)) / den
    intercept = mx - slope * mt
    return intercept + slope * target_s

def predict_absolute_float_seconds(timestamps_ns, positions, horizon_ns):
    times_s = [t / 1_000_000_000.0 for t in timestamps_ns]
    target_s = (timestamps_ns[-1] + horizon_ns) / 1_000_000_000.0
    return _ols_predict(times_s, positions, target_s)

def predict_origin_shifted_delta_seconds(timestamps_ns, positions, horizon_ns):
    origin = timestamps_ns[-1]
    times_s = [(t - origin) / 1_000_000_000.0 for t in timestamps_ns]
    target_s = horizon_ns / 1_000_000_000.0
    return _ols_predict(times_s, positions, target_s)
