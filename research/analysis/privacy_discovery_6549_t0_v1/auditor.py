"""Independent raw-only finite reconstruction and singleton bound check."""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path


def reconstruct(fixture: dict) -> list[dict]:
    rows = []
    for cohort in fixture["cohorts"]:
        for eta in (0, 1, 2):
            classes = []
            counts = cohort["counts"]
            if cohort.get("taxonomy"):
                mapped = {}
                for label, support in counts.items():
                    mapped_label = cohort["taxonomy"].get(label, label)
                    if "|" in mapped_label:
                        mapped[mapped_label] = None
                    elif mapped_label in mapped and mapped[mapped_label] is not None:
                        mapped[mapped_label] += support
                    else:
                        mapped[mapped_label] = support
                counts = mapped
            for label in sorted(counts):
                n = counts[label]
                if n is None:
                    classes.append({"label": label, "support": None, "exact_upper_bound": "NON_PRIVATE",
                        "threshold_status": "UNKNOWN", "noise_eta": eta, "noisy_value": None,
                        "noise_status": "UNKNOWN", "suppression_semantics": "UNKNOWN"})
                    continue
                indeterminate = cohort.get("independence", "independent") != "independent" or bool(cohort.get("duplicate_report_count", 0))
                supported = n >= fixture["threshold"] and not indeterminate
                noisy = max(0, n - eta) if supported else None
                classes.append({"label": label, "support": n, "exact_upper_bound": "NON_PRIVATE",
                    "threshold_status": "UNKNOWN" if n < fixture["threshold"] or indeterminate else "DISCOVERED",
                    "noise_eta": eta, "noisy_value": noisy,
                    "noise_status": "DISCOVERED" if supported and noisy >= fixture["threshold"] else "UNKNOWN",
                    "suppression_semantics": "UNKNOWN"})
            if cohort.get("id") == "no_failure":
                classes = [{"label": None, "support": 0, "exact_upper_bound": "NON_PRIVATE",
                    "threshold_status": "NO_FAILURE_CONTROL", "noise_eta": eta, "noisy_value": 0,
                    "noise_status": "NO_FAILURE_CONTROL", "suppression_semantics": "UNKNOWN"}]
            rows.append({"cohort_id": cohort["id"], "eta": eta, "classes": classes,
                "contribution_cap": fixture["client_cap"],
                "mechanism_claim": "NONE_ASSUMED_NO_DP_GUARANTEE"})
    return rows


def singleton_bound(epsilon: float, delta: float, alpha: float) -> float:
    return math.exp(epsilon) * alpha + delta


def audit(fixture: dict, raw: list[dict]) -> dict:
    expected = reconstruct(fixture)
    errors = []
    if raw != expected:
        errors.append("candidate-differs-from-independent-reconstruction")
    if len(raw) != 24 or len({(r["cohort_id"], r["eta"]) for r in raw}) != len(raw):
        errors.append("denominator-or-key-mismatch")
    if any(r.get("mechanism_claim") != "NONE_ASSUMED_NO_DP_GUARANTEE" or any(c.get("exact_upper_bound") != "NON_PRIVATE" for c in r.get("classes", [])) for r in raw):
        errors.append("privacy-claim-overstated")
    if any(c["suppression_semantics"] != "UNKNOWN" for r in raw for c in r["classes"]):
        errors.append("suppression-not-unknown")
    # Exhaustively check a finite false-report probability grid for the bound.
    eps, delta = fixture["epsilon"], fixture["delta"]
    bound_ok = all(a <= singleton_bound(eps, delta, a) + 1e-15 for i in range(1001) for a in [i / 1000])
    if not bound_ok:
        errors.append("singleton-dp-inequality-mismatch")
    merged = next(c for c in fixture["cohorts"] if c["id"] == "merged")
    merged_support = sum(v for k, v in merged["counts"].items() if merged.get("taxonomy", {}).get(k, k) == "RARE")
    if merged_support != 4:
        errors.append("coarse-taxonomy-support-mismatch")
    return {"errors": errors, "rows": len(raw), "reconstructed_rows": len(expected),
            "singleton_bound_grid_points": 1001, "singleton_bound_max_discovery_at_alpha_0": singleton_bound(eps, delta, 0.0),
            "singleton_alpha_min_for_beta_0_9": (0.9 - delta) / math.exp(eps),
            "merged_rare_support": merged_support,
            "unknown_rows": sum(c["noise_status"] == "UNKNOWN" for r in raw for c in r["classes"]),
            "common_control_detected": all(any(c["label"] == "COMMON" and c["noise_status"] == "DISCOVERED" for c in r["classes"]) for r in raw if r["cohort_id"] == "common" and r["eta"] < 2)}


def corrupt(raw: list[dict], mutation: str) -> list[dict]:
    out = copy.deepcopy(raw)
    if mutation == "omit_client_proxy":
        out.pop()
    elif mutation == "singleton_leak":
        row = next(r for r in out if r["cohort_id"] == "singleton" and r["eta"] == 0)
        next(c for c in row["classes"] if c["label"] == "UNIQUE_SEVERE")["noise_status"] = "DISCOVERED"
    elif mutation == "privacy_claim":
        out[0]["mechanism_claim"] = "DP"
    elif mutation == "suppressed_absent":
        item = next(c for r in out for c in r["classes"] if c["noise_status"] == "UNKNOWN")
        item["suppression_semantics"] = "ABSENT"
    return out


def main() -> None:
    fixture = json.loads(Path(sys.argv[1]).read_text())
    raw = json.loads(Path(sys.argv[2]).read_text())
    report = audit(fixture, raw)
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    raise SystemExit(0 if not report["errors"] else 1)


if __name__ == "__main__":
    main()
