# Issue #6021 T0 — cumulative authority-envelope audit

**Status: `PASS_METHOD_SCOPED`** for the finite synthetic policy algebra only.

The frozen six-case fixture enumerated 256 action/context/effect tuples. Two separately scoped, authenticated field relaxations each yielded no single-change finding and no current-snapshot hard-invariant flag, yet their mechanical conjunction admitted one tuple outside the exact union: `INPUT/R1/T0/S0/stale/matched/verified`. A copied waiver whose history expired at version 2 but remained in the version-3 snapshot was detected. The valid disjoint exceptions and authenticated, scoped supersession remained accepted. The attempted EXPORT waiver admitted zero EXPORT tuples. Evidence requirements shrunk after a HOLD outcome was visible; the prior HOLD was retained and no new PASS was supported.

Seven pre-freeze construction/mutation tests passed. Candidate and independently structured auditor each ran once; both enumerated the finite domain and their expected result fields agreed. Raw stdout is retained under `results/formal-01/`; output SHA-256 values and frozen input hashes are in `RUN.json` and `FREEZE.json`.

## H / T / D / C / U

- **H:** A finite history-aware envelope enumerator detects a cross-product permission and expired exception copied forward while accepting valid scoped exceptions and preserving hard prohibitions.
- **T:** Enumerate 256 action × route × task × source-generation × age × target × effect-truth tuples across six fixtures. Compare mechanically composed scopes with exact authorized-scope unions; track authentication, scope, expiry, supersession, hard invariants, and claim-evidence history. Independently implement the enumeration.
- **D:** `PASS_METHOD_SCOPED`: the interaction and expiry controls were flagged, disjoint and superseding exceptions accepted, the attempted hard-invariant waiver rejected, and post-outcome evidence relaxation detected.
- **C:** No-exception policy-as-code or mandatory direct human diff review may be simpler and more reliable than a cumulative checker.
- **U:** Roles, scopes, histories, and evidence are synthetic. No authenticated real governance, off-repository override, organizational drift frequency, efficacy, or runtime safety is established. A flagged expansion needs human interpretation.

## Execution and limits

Source freeze main was `d6229435f9d651b5309a01dca30c2edd7de2f54a`; see `FREEZE.json` for source hashes. CPython 3.12 host execution only. Docker Desktop was unavailable at Engine level; no container isolation is claimed. No models, external/cloud jobs, GUI, participant, live policy, or real authorization were used. No formal retries or output repair occurred.
