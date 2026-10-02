"""Finite synthetic privacy/discovery frontier; not a privacy mechanism."""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def classify(cohort: dict, threshold: int, eta: int) -> list[dict]:
    counts = cohort["counts"]
    if cohort.get("taxonomy"):
        mapped = {}
        for label, support in counts.items():
            mapped_label = cohort["taxonomy"].get(label, label)
            if "|" in mapped_label:
                # A split label is unresolved; never duplicate its support.
                mapped[mapped_label] = None
            elif mapped_label in mapped and mapped[mapped_label] is not None:
                mapped[mapped_label] += support
            else:
                mapped[mapped_label] = support
        counts = mapped
    out = []
    for label in sorted(counts):
        n = counts[label]
        if n is None:
            out.append({"label": label, "support": None, "exact_upper_bound": "NON_PRIVATE",
                        "threshold_status": "UNKNOWN", "noise_eta": eta, "noisy_value": None,
                        "noise_status": "UNKNOWN", "suppression_semantics": "UNKNOWN"})
            continue
        if cohort.get("independence", "independent") != "independent":
            noisy = None
        elif cohort.get("duplicate_report_count", 0):
            noisy = None
        elif n < threshold:
            noisy = None
        else:
            noisy = max(0, n - eta)
        status = "DISCOVERED" if noisy is not None and noisy >= threshold else "UNKNOWN"
        determinate = cohort.get("independence", "independent") == "independent" and not cohort.get("duplicate_report_count", 0)
        out.append({"label": label, "support": n, "exact_upper_bound": "NON_PRIVATE",
                    "threshold_status": "DISCOVERED" if n >= threshold and determinate else "UNKNOWN",
                    "noise_eta": eta, "noisy_value": noisy,
                    "noise_status": status, "suppression_semantics": "UNKNOWN"})
    if cohort.get("id") == "no_failure":
        out.append({"label": None, "support": 0, "exact_upper_bound": "NON_PRIVATE",
                    "threshold_status": "NO_FAILURE_CONTROL", "noise_eta": eta,
                    "noisy_value": 0, "noise_status": "NO_FAILURE_CONTROL",
                    "suppression_semantics": "UNKNOWN"})
    return out


def run(fixture: dict) -> list[dict]:
    rows = []
    for cohort in fixture["cohorts"]:
        for eta in (0, 1, 2):
            rows.append({"cohort_id": cohort["id"], "eta": eta,
                         "classes": classify(cohort, fixture["threshold"], eta),
                         "contribution_cap": fixture["client_cap"],
                         "mechanism_claim": "NONE_ASSUMED_NO_DP_GUARANTEE"})
    return rows


def main() -> None:
    fixture = json.loads(Path(sys.argv[1]).read_text())
    raw = run(fixture)
    Path(sys.argv[2]).write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"allocation": fixture["allocation"], "rows": len(raw)}, sort_keys=True))


if __name__ == "__main__":
    main()
