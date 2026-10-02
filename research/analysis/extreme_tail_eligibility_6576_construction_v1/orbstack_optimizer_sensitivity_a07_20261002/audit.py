"""Independent raw-only audit of A07 samples, masks and GPD likelihoods."""
import hashlib
import json
import math
import statistics
import sys
from pathlib import Path

root = Path(sys.argv[1])
cfg = json.loads((root / "prereg.json").read_text())
r_raw = json.loads((root / "output/r.raw.json").read_text())
py_raw = json.loads((root / "output/python.raw.json").read_text())
errors, summaries = [], []
variants = {v["name"] for v in cfg["r_fit_variants"]}


def type7(values, p):
    ordered = sorted(values)
    h = (len(ordered) - 1) * p
    lo = math.floor(h)
    frac = h - lo
    return ordered[lo] + frac * (ordered[min(lo + 1, len(ordered) - 1)] - ordered[lo])


def nll(excesses, scale, shape):
    if not math.isfinite(scale) or scale <= 0:
        return math.inf
    total = len(excesses) * math.log(scale)
    for value in excesses:
        support = 1 + shape * value / scale
        if not math.isfinite(support) or support <= 0:
            return math.inf
        total += value / scale if abs(shape) < 1e-8 else (1 + 1 / shape) * math.log(support)
    return total


if len(r_raw.get("rows", [])) != len(cfg["seeds"]) or len(py_raw.get("rows", [])) != len(cfg["seeds"]):
    errors.append("candidate cardinality mismatch")
r_by_seed = {row.get("seed"): row for row in r_raw.get("rows", [])}
py_by_seed = {row.get("seed"): row for row in py_raw.get("rows", [])}
for seed in cfg["seeds"]:
    raw = (root / "input" / f"{seed}.txt").read_bytes()
    sample = [float(v) for v in raw.decode().splitlines()]
    sample_hash = hashlib.sha256(raw).hexdigest()
    threshold = type7(sample, cfg["threshold_probability"])
    candidates = sorted(range(len(sample)), key=lambda i: sample[i], reverse=True)[:cfg["candidate_count"]]
    excluded = set(candidates)
    excesses = [v - threshold for i, v in enumerate(sample) if i not in excluded and v > threshold]
    rr, pp = r_by_seed.get(seed), py_by_seed.get(seed)
    if rr is None or pp is None:
        errors.append(f"seed {seed}: candidate row missing")
        continue
    for label, row in (("R", rr), ("Python", pp)):
        if row.get("sample_sha256") != sample_hash:
            errors.append(f"seed {seed}: {label} sample hash mismatch")
        if row.get("candidate_indices") != [i + 1 for i in candidates]:
            errors.append(f"seed {seed}: {label} candidate mask mismatch")
        if not math.isclose(float(row.get("threshold", math.nan)), threshold, rel_tol=0, abs_tol=1e-12):
            errors.append(f"seed {seed}: {label} threshold mismatch")
    fits = rr.get("fits", [])
    if {f.get("name") for f in fits} != variants or len(fits) != len(variants):
        errors.append(f"seed {seed}: R variant set mismatch")
    valid = []
    for fit in fits:
        if "error" in fit or fit.get("convergence") != 0 or len(fit.get("mle", [])) != 2:
            errors.append(f"seed {seed} {fit.get('name')}: incomplete/nonconverged fit")
            continue
        scale, shape = map(float, fit["mle"])
        computed = nll(excesses, scale, shape)
        if not math.isclose(computed, float(fit["nll"]), rel_tol=0, abs_tol=2e-5):
            errors.append(f"seed {seed} {fit['name']}: reported likelihood mismatch")
        valid.append((scale, shape, computed, fit["name"]))
    if len(valid) != len(variants):
        continue
    scales, shapes, objectives = ([v[i] for v in valid] for i in range(3))
    scale_range = (max(scales) - min(scales)) / statistics.median(scales)
    shape_range, nll_range = max(shapes) - min(shapes), max(objectives) - min(objectives)
    default = next(f for f in fits if f["name"] == "default_nm")
    rscale, rshape = map(float, default["mle"])
    pscale, pshape = float(pp["scale"]), float(pp["shape"])
    rel_scale = abs(rscale - pscale) / abs(rscale)
    abs_shape = abs(rshape - pshape)
    gate = cfg["r_sensitivity_gate"]
    parity = cfg["r_python_parity_gate"]
    summaries.append({"seed": seed, "exceedance_count": len(excesses),
                      "relative_scale_range": scale_range, "shape_range": shape_range,
                      "nll_range": nll_range, "r_optimizer_sensitive":
                      scale_range > gate["relative_scale_range_max"] or shape_range > gate["shape_range_max"] or nll_range > gate["nll_range_max"],
                      "r_python_relative_scale_delta": rel_scale,
                      "r_python_absolute_shape_delta": abs_shape,
                      "r_python_within_gate": rel_scale <= parity["relative_scale_max"] and abs_shape <= parity["absolute_shape_max"]})

if errors or len(summaries) != len(cfg["seeds"]):
    print("AUDIT_INVALID")
    print("\n".join(errors or ["summary coverage incomplete"]))
    raise SystemExit(2)
print("AUDIT_VALID")
for row in summaries:
    print(json.dumps(row, sort_keys=True, separators=(",", ":")))
print("R_OPTIMIZER_SENSITIVE=" + str(any(r["r_optimizer_sensitive"] for r in summaries)))
print("PYTHON_NUMERICAL_PARITY=" + str(all(r["r_python_within_gate"] for r in summaries)))
