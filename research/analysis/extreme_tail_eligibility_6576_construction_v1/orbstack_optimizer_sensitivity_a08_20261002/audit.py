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
    failed_variants = []
    for fit in fits:
        if "error" in fit:
            failed_variants.append({"name": fit.get("name"), "status": "error",
                                    "detail": fit.get("error")})
            continue
        if fit.get("convergence") != 0:
            failed_variants.append({"name": fit.get("name"), "status": "nonconverged",
                                    "code": fit.get("convergence")})
            continue
        if len(fit.get("mle", [])) != 2:
            errors.append(f"seed {seed} {fit.get('name')}: converged fit missing parameters")
            continue
        scale, shape = map(float, fit["mle"])
        computed = nll(excesses, scale, shape)
        if not math.isclose(computed, float(fit["nll"]), rel_tol=0, abs_tol=2e-5):
            errors.append(f"seed {seed} {fit['name']}: reported likelihood mismatch")
        valid.append((scale, shape, computed, fit["name"]))
    default = next((v for v in valid if v[3] == cfg["r_sensitivity_gate"]["required_default"]), None)
    classifiable = default is not None and len(valid) >= cfg["r_sensitivity_gate"]["minimum_converged_fits"]
    if classifiable:
        scales, shapes, objectives = ([v[i] for v in valid] for i in range(3))
        scale_range = (max(scales) - min(scales)) / statistics.median(scales)
        shape_range, nll_range = max(shapes) - min(shapes), max(objectives) - min(objectives)
        rscale, rshape = default[0], default[1]
        pscale, pshape = float(pp["scale"]), float(pp["shape"])
        rel_scale = abs(rscale - pscale) / abs(rscale)
        abs_shape = abs(rshape - pshape)
    else:
        scale_range = shape_range = nll_range = rel_scale = abs_shape = None
    gate = cfg["r_sensitivity_gate"]
    parity = cfg["r_python_parity_gate"]
    sensitive = None if not classifiable else (
        scale_range > gate["relative_scale_range_max"] or
        shape_range > gate["shape_range_max"] or nll_range > gate["nll_range_max"])
    within_parity = None if not classifiable else (
        rel_scale <= parity["relative_scale_max"] and
        abs_shape <= parity["absolute_shape_max"])
    summaries.append({"seed": seed, "exceedance_count": len(excesses),
                      "converged_variant_names": [v[3] for v in valid],
                      "failed_variants": failed_variants,
                      "classifiable": classifiable,
                      "relative_scale_range": scale_range, "shape_range": shape_range,
                      "nll_range": nll_range, "r_optimizer_sensitive": sensitive,
                      "r_python_relative_scale_delta": rel_scale,
                      "r_python_absolute_shape_delta": abs_shape,
                      "r_python_within_gate": within_parity})

if errors or len(summaries) != len(cfg["seeds"]):
    print("AUDIT_INVALID")
    print("\n".join(errors or ["summary coverage incomplete"]))
    raise SystemExit(2)
print("AUDIT_VALID")
for row in summaries:
    print(json.dumps(row, sort_keys=True, separators=(",", ":")))
if not all(row["classifiable"] for row in summaries):
    print("DISPOSITION=INCONCLUSIVE_INSUFFICIENT_CONVERGED_VARIANTS")
else:
    print("DISPOSITION=" + ("R_OPTIMIZER_SENSITIVE" if any(r["r_optimizer_sensitive"] for r in summaries)
                             else "R_FITS_STABLE_AT_GATE"))
print("PYTHON_NUMERICAL_PARITY=" + str(all(r["r_python_within_gate"] is True for r in summaries)))
