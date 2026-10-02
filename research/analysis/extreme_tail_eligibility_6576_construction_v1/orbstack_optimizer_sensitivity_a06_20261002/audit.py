"""Independent raw-only audit for the frozen A06 optimizer comparison."""
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1])
r_raw = json.loads((root / "output/r.raw.json").read_text())
py_raw = json.loads((root / "output/python.raw.json").read_text())
seeds = (65769931, 65769932, 65769933, 65769934, 65769935, 65769936)
expected_names = {"default_nm", "nm_1_0", "nm_2_neg075", "nm_05_neg125",
                  "default_bfgs", "bfgs_1_0"}
errors = []
rows = []


def nll(excesses, scale, shape):
    if not math.isfinite(scale) or scale <= 0:
        return math.inf
    total = len(excesses) * math.log(scale)
    for value in excesses:
        support = 1 + shape * value / scale
        if support <= 0 or not math.isfinite(support):
            return math.inf
        if abs(shape) < 1e-8:
            total += value / scale
        else:
            total += (1 + 1 / shape) * math.log(support)
    return total


def type7(values, probability):
    ordered = sorted(values)
    h = (len(ordered) - 1) * probability
    lo = math.floor(h)
    frac = h - lo
    return ordered[lo] + frac * (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo])


if len(r_raw.get("rows", [])) != len(seeds) or len(py_raw.get("rows", [])) != len(seeds):
    errors.append("candidate row cardinality mismatch")
r_by_seed = {row.get("seed"): row for row in r_raw.get("rows", [])}
py_by_seed = {row.get("seed"): row for row in py_raw.get("rows", [])}
for seed in seeds:
    sample_path = root / "input" / f"{seed}.txt"
    raw = sample_path.read_bytes()
    sample = [float(line) for line in raw.decode().splitlines()]
    digest = hashlib.sha256(raw).hexdigest()
    threshold = type7(sample, 0.90)
    candidates = sorted(range(len(sample)), key=lambda i: sample[i], reverse=True)[:2]
    excesses = [value - threshold for i, value in enumerate(sample)
                if i not in set(candidates) and value > threshold]
    rrow, pyrow = r_by_seed.get(seed), py_by_seed.get(seed)
    if not rrow or not pyrow:
        errors.append(f"seed {seed}: missing candidate row")
        continue
    if rrow.get("sample_sha256") != digest or pyrow.get("sample_sha256") != digest:
        errors.append(f"seed {seed}: sample hash mismatch")
    if rrow.get("candidate_indices") != [i + 1 for i in candidates]:
        errors.append(f"seed {seed}: R candidate indices mismatch")
    if pyrow.get("candidate_indices") != [i + 1 for i in candidates]:
        errors.append(f"seed {seed}: Python candidate indices mismatch")
    if not math.isclose(rrow.get("threshold", math.nan), threshold, rel_tol=0, abs_tol=1e-12):
        errors.append(f"seed {seed}: R threshold mismatch")
    if not math.isclose(pyrow.get("threshold", math.nan), threshold, rel_tol=0, abs_tol=1e-12):
        errors.append(f"seed {seed}: Python threshold mismatch")
    fits = rrow.get("fits", [])
    names = {fit.get("name") for fit in fits}
    if names != expected_names or len(fits) != len(expected_names):
        errors.append(f"seed {seed}: R fit variant mismatch")
    valid = []
    for fit in fits:
        if fit.get("error") is not None:
            errors.append(f"seed {seed} {fit.get('name')}: candidate optimizer error")
            continue
        mle = fit.get("mle", [])
        if fit.get("convergence") != 0 or len(mle) != 2:
            errors.append(f"seed {seed} {fit.get('name')}: nonconverged/incomplete fit")
            continue
        recomputed = nll(excesses, float(mle[0]), float(mle[1]))
        if not math.isclose(recomputed, float(fit["nll"]), rel_tol=0, abs_tol=2e-5):
            errors.append(f"seed {seed} {fit.get('name')}: R likelihood not independently reproducible")
        valid.append((float(mle[0]), float(mle[1]), recomputed, fit.get("name")))
    if len(valid) == len(expected_names):
        scales = [v[0] for v in valid]
        shapes = [v[1] for v in valid]
        nlls = [v[2] for v in valid]
        rel_scale_range = (max(scales) - min(scales)) / statistics.median(scales)
        shape_range = max(shapes) - min(shapes)
        nll_range = max(nlls) - min(nlls)
    else:
        rel_scale_range = shape_range = nll_range = math.inf
    py_nll = nll(excesses, float(pyrow["scale"]), float(pyrow["shape"]))
    default = next((fit for fit in fits if fit.get("name") == "default_nm"), {})
    rscale, rshape = (default.get("mle") or [math.nan, math.nan])
    rel_scale_delta = abs(float(rscale) - float(pyrow["scale"])) / abs(float(rscale))
    shape_delta = abs(float(rshape) - float(pyrow["shape"]))
    rows.append({"seed": seed, "exceedance_count": len(excesses),
                 "r_relative_scale_range": rel_scale_range,
                 "r_shape_range": shape_range, "r_nll_range": nll_range,
                 "default_r_python_relative_scale_delta": rel_scale_delta,
                 "default_r_python_shape_delta": shape_delta,
                 "default_r_nll": nll(excesses, float(rscale), float(rshape)),
                 "python_nll": py_nll,
                 "r_optimizer_sensitive": rel_scale_range > 0.001 or shape_range > 0.001 or nll_range > 1e-6,
                 "python_parity_within_a05_limits": rel_scale_delta <= 0.001 and shape_delta <= 0.001})

if errors:
    print("AUDIT_INVALID")
    print("\n".join(errors))
    raise SystemExit(2)
print("AUDIT_VALID")
for row in rows:
    print(json.dumps(row, sort_keys=True, separators=(",", ":")))
print("R_OPTIMIZER_SENSITIVE=" + str(any(row["r_optimizer_sensitive"] for row in rows)))
print("A05_PYTHON_NUMERICAL_PARITY=" + str(all(row["python_parity_within_a05_limits"] for row in rows)))
