# Issue #8909 A01 — protective-control diagnosability trace audit

**Status:** `PASS_METHOD_SCOPED`; `MASK_WITNESS_SCOPED` and `RESTORATION_SCOPED` for this authored model only. This is not an Agent Interface runtime, GUI, or efficacy result.

## Freeze and execution

- Repository base: `main` at `964c9197d5083ab55ea7fdc9105427623e89e677` (2026-10-12).
- Hypothesis owner: [Issue #8909](https://github.com/Unjuno/agent-interface/issues/8909).
- Candidate source: `a01.mjs`; dependency-free ES module / Node-compatible script.
- Execution 1 (session construction): exact source evaluated in the JavaScript V8 isolate with `process` unavailable; no filesystem, GUI, model, or container was used.
- Execution 2 (reproduction): fetched this branch's raw `a01.mjs` and piped it directly to Windows Node `v24.6.0` (`curl.exe ... | node -`); exit code 0 and stdout matched the retained `result.json` fields. No local source/evidence file was created. For reproduction, run `node a01.mjs`.
- Frozen state space: 5 states × 3 policies, horizon 2 observation ticks = 15 traces.
- Policies: no-cover; protective-cover; protective-cover plus passive sentinel.
- Independent oracle: separately authored literal state/event table and trace calculation; it does not call candidate transition/enumeration code. The checker compares every trace, safety prefix and next-response label and separately checks the predeclared equivalence pairs.

## Preserved construction failure

The first construction attempt failed before the formal A01 check. Its candidate encoded cover eligibility as “fault-A or fault-B,” while the independent table also marked `out-of-catalog` as covered. The first mismatch was `protective-cover/out-of-catalog` (`trace/oracle mismatch`). This exposed a candidate/oracle fixture inconsistency, not a scientific counterexample. It is retained here rather than counted as PASS or silently overwritten. The corrected candidate uses an explicit `covered` factor and the literal oracle agrees on all 15 rows.

## Results

- A/B require incompatible next actions (`yield-left` vs `yield-right`). They are distinguishable without cover, become trace-equivalent under protective cover, and are distinguished again by the sentinel policy.
- C/D require the same next action (`continue`). Their traces remain distinct, confirming the positive-control signal; if they were aliased, diagnosis would not be decision-relevant under this frozen response table.
- No enumerated prefix leaves the declared safe set (0 unsafe prefixes).
- Out-of-catalog remains explicitly `UNKNOWN`; the test does not claim to diagnose its hidden cause.
- Five mutations were rejected: dropped state/policy row, forged sentinel, unsafe prefix, truncated horizon, and changed out-of-catalog response.
- Raw machine-readable outcome: `result.json`.

## H/T/D/C/U disposition

- **H:** supported only as an existence witness in this constructed deterministic model: cover can preserve its modeled safety bit while collapsing evidence needed for different next actions; a truthful sentinel can restore separation.
- **T:** completed as exhaustive finite enumeration and independent-table audit.
- **D:** method gate passes for the authored table; the masking and restoration labels are scoped model outcomes only. No real-system gate was attempted.
- **C:** robust control may make fault identification unnecessary when a common safe response covers the ambiguity; C/D encode this distinction.
- **U:** labels, transition relation, cover mask and sentinel truth are authored assumptions. No sensor common-cause/provenance, stochastic behavior, real GUI, runtime timing, task effect, or prevalence is modeled.

## Reproduction and handoff

This artifact is additive and isolated under `research/analysis/issue_8909_cover_diagnosability_a01_20261012/`. The same committed source also passed direct execution under Windows Node v24.6.0 as described above. No WSL distro/runtime-specific validation was possible in this session. This report does not close #8909 or justify runtime changes. WSL 3.0.1 is installed, but the currently selected Ubuntu distro failed its startup I/O/user-resolution preflight in this session; therefore this CPU-only calculation used no WSL/container boundary. The separate migration/performance study is not implicated.


## Repository CI finding (preserved)

The first GitHub Actions run on head `8fa7b512ff366deb1e8db3017838107f0ee7eedc` had `replay-gate=success` and `analysis-index=failure`. The index job passed its three selected archival tests, then `research/analysis/check_index.py` reported this new retained result directory missing from the generated index. This was a publication-index omission, not a candidate/scientific failure. The canonical sorted entry was added to `research/analysis/README.md` on the PR branch; the regenerated-index check has not yet been observed on the resulting head at report time. Keep the first failure in the record.
