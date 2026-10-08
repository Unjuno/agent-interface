# Issue #5841 T1 — path-specific negative-control construction

## Outcome

**`PASS_METHOD_SCOPED_WITH_KNOWN_ESCAPE`** — seven finite synthetic cases and 56 assignment rows completed, with one frozen candidate subprocess and one independent raw auditor subprocess. The declared shared-path fault was detected by a same-cohort sentinel despite passing the existing all-attempt completeness/identity checks. A primary-only fault was *not* detected by either comparator and is preserved as `OUT_OF_SCOPE_UNDETECTED`. This is a narrow construction result, not a general validation of negative controls.

| Case | All-attempt | Sentinel A→B | Primary A→B | Disposition |
|---|---|---:|---:|---|
| Clean null | PASS_COMPLETE | 0.00→0.00 | 0.50→0.50 | NO_SIGNAL |
| True primary benefit | PASS_COMPLETE | 0.00→0.00 | 0.50→1.00 | NO_SIGNAL |
| Shared export fault | PASS_COMPLETE | 0.00→0.25 | 0.50→0.75 | SHARED_PATH_HOLD |
| Primary-only fault | PASS_COMPLETE | 0.00→0.00 | 0.50→0.75 | OUT_OF_SCOPE_UNDETECTED |
| Missing terminal | HOLD_MISSING | 0.00→0.00 | 0.50→0.67* | MISSING_HOLD |
| Foreign join | HOLD_IDENTITY | 0.00→0.00 | 0.50→0.50 | IDENTITY_HOLD |
| Real sentinel collateral | PASS_COMPLETE | 0.00→0.25 | 0.50→0.50 | COLLATERAL_FAIL |

`*` The complete-case rate is displayed only to expose the arithmetic; the missingness hold forbids interpreting it as an effect estimate. The sentinel is a route-rate contrast, not a comparison to the hidden synthetic ground truth. Ground truth is used only by the separate adjudication oracle to classify shared measurement error versus real collateral.

## Audit and reproducibility

- Source freeze: `FREEZE.json`; source base `main` SHA `2fbbd0430359a2de11609372e003c3f6ad632a36`.
- Construction checks before freeze: pytest 1/1, py_compile passed, fixture/freeze JSON parsed, all frozen SHA-256 source identities verified.
- Candidate: `python execute_once.py`, one invocation, 7 cases / 56 rows; raw output at `results/candidate.stdout.json`, SHA-256 `0673f01a93d77d8aa8b940e22006e7af56a8421a87bfbb0e25e4d0269d735a02`.
- Independent auditor: `python audit_once.py`, one invocation; `PASS_INDEPENDENT_AUDIT`, zero errors; omitted-case and false-all-clear relabel mutation controls both rejected. `results/AUDIT.json`, SHA-256 `424a037aeeae454cd100c7e474e9de6661875dd95e5b6bb0df0edc54349265be`.
- Host: Windows 11 Home 10.0.26200 AMD64; CPython 3.12.10. No repository runtime or application was imported.

## Docker and execution boundary

Docker Desktop was explicitly checked. The `desktop-linux` context exists and its UI process was present, but `com.docker.service` was stopped/manual. `docker version --format '{{.Server.Version}}'` timed out; attempting to start the service failed with “Cannot open 'com.docker.service' service on computer '.'”. No container started, no image identity exists, and no privilege workaround was attempted. The experiment therefore ran host-only; it is not presented as container-validated.

## H / T / D / C / U

- **H:** Same-cohort negative controls add detection only for declared faults that share the sentinel observation/export path; they do not establish general absence of primary-endpoint bias.
- **T:** Seven isolated cases, four assignments per route, 56 rows. `FREEZE.md` records the path diagram and preregistered classification rules. Faults cover clean null, true benefit, shared export, primary-only export, missing terminal, foreign join and real collateral.
- **D:** Shared fault detected when all-attempt reconciliation passes; primary-only fault explicitly escapes; missing and foreign join stopped by the simpler existing comparator; real collateral classified separately; two auditor mutations rejected. All criteria were met for this finite construction.
- **C:** All-attempt reconciliation is the sufficient/simple detector for missingness and ID/route integrity. Sentinel adds a signal only for the deliberately shared exporter fault in this fixture. This confirms the Issue’s narrow value proposition, not superiority across generic faults.
- **U:** The synthetic pipeline does not establish that any production scorer shares these exact stages, that a real sentinel is route-invariant, or that the independent truth oracle is available operationally. Small finite counts say nothing about sensitivity, false-positive rates, or live #57 outcomes. The previously reported primary-only false all-clear remains a hard limitation.

## Disposition

This is a successor to, not a replacement for, the earlier Issue #5841 T0 and exploratory comment #5925853020. It did not modify the earlier result package. Do not close #5841 or promote this to empirical/runtime evidence. Any next step against a real scoring path needs a frozen data-flow map for primary and sentinel, a defensible invariant with independent collateral adjudication, and a predeclared comparison against all-attempt reconciliation.
