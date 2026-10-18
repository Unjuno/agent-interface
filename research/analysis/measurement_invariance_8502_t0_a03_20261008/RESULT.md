# Issue #8502 T0 A03 — `PASS_METHOD_SCOPED`

## H / T / D / C / U

- **H:** A coarse ordinal-response screen can flag large planted threshold, item-loading-pattern, and factor-structure shifts, accept the invariant control at fixed margins, and return `UNCERTAIN` for the sparse control.
- **T:** Five fresh deterministic two-group, six-item, five-category fixtures; seeds 850301–850305; 1,500 responses/group except 20/group for F05. Candidate and independently implemented raw-only contingency-table auditor each ran once after freeze; zero retries. Python 3.12.10, local CPU, standard library only.
- **D:** `PASS_METHOD_SCOPED`: five of five predeclared classifications/localizations match; the independent auditor reconstructed all rows with zero errors; all six in-memory semantic/integrity mutations were rejected. A01 and A02 remain separately preserved as `FAIL_METHOD` and `FAIL_AUDIT_ONLY`; A03 does not rewrite or execute them.
- **C:** These are authored synthetic distributions with large shifts, fixed margins and fixed seeds. The simple ordinal/correlation screen can miss subtle DIF, confuse real latent-distribution changes with measurement changes, or misclassify other covariance structures.
- **U:** Synthetic method evidence only. No human responses, workload construct validation, ordinal CFA/IRT, scalar invariance, latent-mean comparability, accessibility, user benefit, GUI, model, runtime, or safety claim. `COMPATIBLE_SCREEN` is not permission to compare human means.

## Formal outcome

| Fixture | Candidate and independent result | Reconstructed detail |
|---|---|---|
| F01 invariant control | `COMPATIBLE_SCREEN` | Maximum paired-cutpoint gaps 0.0147–0.0207; no association edge crossed 0.22. |
| F02 threshold shift | `THRESHOLD_NONINVARIANCE`, item 2 | Item-2 maximum paired-CDF gap 0.2653; all other item gaps ≤0.0380. |
| F03 loading change | `LOADING_PATTERN_NONINVARIANCE`, item 2 | Five changed association edges, all incident to item 2; no threshold item. |
| F04 structure change | `STRUCTURE_NONINVARIANCE` | Nine changed cross-block edges; no single shared item; no threshold item. |
| F05 sparse control | `UNCERTAIN` | 20/group is below the frozen minimum 100; effect screen is not used. |

The independent audit reports zero errors and rejects all six controls: wrong class, wrong threshold localization, sparse-as-compatible, missing result, wrong seed, and tampered input digest. Candidate output SHA-256 is `49570a235b0b58d1ce4711c73ee6fcd2d3fa36006e1b4741aba55cc722d20ca0`; auditor output SHA-256 is `6cabcd53f75478e7771192e8152ebacd94dd1fd1bbafc7189c76398a4cf7ee43`.

## Provenance and disposition

Frozen base main: `e627b8954ecfbdd90ccfe35a81441a00d88047c8`. Freeze SHA-256: `9d55eddefd971dde08bb03e634fba0a2c4998ee39b404717b7cf2034c4811d83`. Fixture SHA-256: `63e02be00018be60637f10a070bc2ff76310077c507916cccc978509bfaa3c91`. Truth SHA-256: `a35d7f1c615f272c3b4332ea334f8a6e50710c1d49ea65da4093854f668ad757`. See `FREEZE.json`, `RUN.json`, `AUDIT.json`, and `SHA256SUMS.json` for complete source/runtime/command identities.

This A03 successor corrects A01's paired-cutpoint estimator and A02's source-digest freeze process, while using distinct seeds. Neither correction changes A01/A02's historical outcomes. This remains a finite synthetic screen, not evidence that real human workload scores are comparable.

The task directory was not a clean current-main Git checkout. Local construction tests and syntax compilation ran here; repository index checks and required integration checks are delegated to the reviewable PR's GitHub Actions. No WSLc/Docker invocation occurred: the frozen T0 requires only a finite standard-library CPU calculation, not an image boundary, and the shared WSLc ownership HOLD remains a separate unresolved coordination item.

## Reproduction

To reproduce this method without overwriting retained outputs, copy the whole package to a new empty directory first. In that copy, on Python 3.12.10, run from the copy's directory; the freeze will receive a new timestamp and therefore a new freeze hash, while the fixed fixtures and method source bytes remain reproducible:

```powershell
python -B generate.py --out-dir .
python -B freeze.py --main-sha e627b8954ecfbdd90ccfe35a81441a00d88047c8
python -B candidate.py --dir .
python -B audit.py --dir .
```

Formal output files use exclusive creation. The recorded allocation is one candidate and one auditor invocation with zero retries; rerunning into the same package is expected to stop rather than overwrite these outcomes.
