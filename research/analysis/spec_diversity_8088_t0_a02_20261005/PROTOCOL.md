# Issue #8088 — T0 A02 successor

Allocation: `SPEC-DIVERSITY-8088-T0-A02-20261005-01`. Fresh branch from current `main`; additive package path. A01 remains unchanged in its own branch and its formal output is not reused as A02 output.

## H / T / D / C / U

- **H:** With all explicit obligations bound to observable raw fields, the same two frozen decompositions still produce no qualifying omission mutant beyond ordinary controls; specifically, both the primary scorer and raw-only auditor reject an implementation that preserves records but fails to restore all visible rows after selecting All.
- **T:** Reuse only A01’s immutable synthetic contracts, decompositions, and blinded adjudication as preregistered inputs. Add an obligation-to-raw-field coverage matrix before code freeze. Candidate emits before/after records and visible ID snapshots for Active and All; independently authored raw-only auditor reconstructs all obligations from those snapshots. Freeze five ordinary controls (A01 four plus the C06 visibility-preservation fault), code, tests, and hashes before one candidate and one auditor invocation. No omission mutants are generated unless adjudication names an explicit divergence; A01 adjudicated none.
- **D:** `NO_INCREMENTAL_VALUE_SCOPED` only if every explicit obligation maps to raw, all eight baseline contracts pass, all five ordinary controls fail for their named clauses, no non-target clause is broken, and independent audit reconstructs every clause. `HOLD_BASELINE_ORACLE_COVERAGE` if any explicit clause lacks observable raw support or independent reconstruction. `FAIL` if a declared expected fault survives or any ambiguity is promoted to fact. A formal run failure remains one-shot; no rerun.
- **C:** The extra C06 control may be detectable by ordinary contract-derived auditing and may add no specification-diversity value; the two decompositions may omit the same unresolved assumptions.
- **U:** Same eight synthetic, AI-authored contracts and previously adjudicated decomposition pair only. No human/model-family independence, app behavior, real-user intent, production common-mode rate, or general efficacy claim.

## Frozen predecessor inputs

A01’s published challenge preceded primary-output retrieval. Its separate-context authors and blinded adjudicator used the same configured assistant service; these roles do not establish human or model-family independence. Reuse preserves the author outputs, not A01’s invalid C06 formal conclusion. The JSON contract content is unchanged; transfer normalized one terminal blank line, and A02 binds its actual contract bytes in the coverage matrix. Predecessor branch: `research/spec-diversity-8088-t0-a01-20261005`; predecessor PR #8191 currently records `HOLD_BASELINE_ORACLE_COVERAGE`.

## Runtime

Stdlib CPU-only method packet. A01 already established on this same host that Docker 29.4.0 `linux/aarch64` image inspection of `python:3.12-slim` fails with containerd blob `operation not supported`. Do not repeat that unchanged preflight; use native macOS Python, make no container-isolation claim, and do not repair/prune/restart the shared daemon.
