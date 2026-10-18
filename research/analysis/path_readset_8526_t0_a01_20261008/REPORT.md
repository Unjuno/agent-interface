# Issue #8526 — path-conditioned read sets (T0 A01)

**Result: `PASS_PATH_CONDITIONED_READSET_SCOPED`.** In this 13-scenario deterministic fixture, a complete `PATH_CERTIFICATE` safely retained two results after changes confined to unexecuted branch fields that `GLOBAL_UNION` conservatively invalidated. It made zero false accepts across the frozen controls, and the independent auditor rejected all three path/provenance/generation mutations. The simpler `EXECUTED_PATH` baseline falsely accepted the hidden-read case when instrumentation was incomplete.

This is a finite synthetic method result only. It does not show that real model, prompt, GUI, document or application computations expose complete dependency provenance; does not authorize an action; and does not establish runtime correctness, latency/token gains, reliability, portability or product benefit.

## Frozen comparison and outcome

The same 13 schedules were evaluated under `GLOBAL_UNION`, `EXECUTED_PATH`, and `PATH_CERTIFICATE` (39 total rows). Independent reconstruction used a separate literal oracle and did not import `candidate.py`.

| Policy | Correct safe accepts | Safe invalidations | False accepts | Interpretation |
| --- | ---: | ---: | ---: | --- |
| `GLOBAL_UNION` | 2/4 | 2 | 0 | Conservative; rejects both safe unexecuted-branch changes. |
| `EXECUTED_PATH` | 4/4 | 0 | 1 | Selective, but accepts the hidden-read result despite incomplete instrumentation. |
| `PATH_CERTIFICATE` | 4/4 | 0 | 0 | Retains both safe cases and refuses the incomplete/unsafe controls. |

The two safe salvages were (1) a changed inactive `beta` leaf while branch A remained current, and (2) an unknown inactive `alpha` leaf while branch B remained current. The hidden-read fixture's hidden truth was available only to the auditor; the candidate received an incomplete-instrumentation flag and no hidden value. All policies rejected a changed active leaf, route change, unknown route, unknown active input, and unknown predicate provenance. Global union and PATH_CERTIFICATE rejected incomplete dependency coverage; all policies rejected source-epoch/ABA change, producer-generation change and expired deadline.

The audit summary reports 39/39 reconstructed rows, zero PATH_CERTIFICATE false accepts, and 3/3 rejected mutations. It also reports `checked_fields_by_policy`: global union 104, executed path 78, path certificate 104. Thus this fixture shows a selectivity/soundness boundary, **not** lower validation work for the certificate path; no timing or cost endpoint was measured.

## H / T / D / C / U

- **H:** A complete typed path certificate can salvage valid late results rejected solely for an unexecuted-branch change, without accepting any frozen stale/unknown/hidden/generation/deadline control.
- **T:** Frozen 13-case × 3-policy deterministic synthetic comparison; native Windows CPython 3.12.10, no model, GUI, network, OS-observation input, WSLc, or Docker.
- **D:** Pass gate required exact fixture reconstruction, ≥2 safe salvages, 0 PATH_CERTIFICATE false accepts and rejection of 3/3 audit mutations. All gates were met. Candidate: one invocation, exit 0. Independent auditor: one invocation, exit 0. No retry.
- **C:** Complete `GLOBAL_UNION` remains a conservative option; `EXECUTED_PATH` is unsafe when a hidden read is not in its declared footprint; this fixture omits costs of building/reviewing certificates. The candidate checks no fewer recorded fields than global union here.
- **U:** One authored finite model; no evidence that real computation read sets are complete or that savings exceed certificate overhead. No GUI/task effect, authority, performance, reliability, portability or production claim.

## Reproduction and retained evidence

See [the exact run record](RUN_RECORD.md), [the frozen source/protocol digests](FREEZE.json), and [the protocol](PROTOCOL.md). Raw candidate and audit outputs are retained in `results/candidate.json` and `results/audit.json`. Construction tests passed 9/9 before freeze; they are not counted as formal runs. `SHA256SUMS` covers the published package files.
