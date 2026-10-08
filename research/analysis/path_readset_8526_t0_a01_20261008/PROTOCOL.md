# Issue #8526 T0 A01 — path-conditioned semantic read-set discriminator

## H / T / D / C / U

**H.** In this deterministic typed fixture, `PATH_CERTIFICATE` accepts at least one correct late result rejected by `GLOBAL_UNION` solely because a dependency on an unexecuted branch changed, while refusing each frozen path-switch, unknown, hidden-read, ABA/source-epoch, producer-generation, and deadline control. Its accepted set has zero false accepts against the independent finite oracle.

**T.** Compare three validation contracts over identical frozen transition records: `GLOBAL_UNION` validates all declared branch fields; `EXECUTED_PATH` validates the recorded predicate and active leaf but deliberately does not require complete dependency instrumentation; `PATH_CERTIFICATE` validates that executed path plus explicit completeness, predicate provenance, source epoch, producer generation, deadline, and result binding. Rejected outputs are private proposals only; the fixture emits no authority or action.

**D.** The frozen matrix contains 13 cases × 3 policies = 39 rows. The 13 cases are: stable A path; stable B path; changed unexecuted B field on A; unknown unexecuted A field on B; changed executed leaf; changed route predicate; unknown predicate; unknown active input; incomplete certificate from a hidden read; unknown predicate provenance; source-epoch change-and-return (ABA); producer-generation change; and expired deadline. The hidden-state truth for the hidden-read case exists only in the independent auditor's literal oracle fixture, not in candidate input.

The auditor independently reconstructs every visible fixture and expected decision, and compares the accepted set with a literal safe-case set. It also rejects three evidence mutations: deletion of the route predicate from a salvaged certificate, relabeling an A-path result as B, and deletion of its source-epoch binding. It reports false accepts and unnecessary invalidations per policy plus the number of recorded validation fields. No timing, cost, or performance claim is tested.

**Decision.** `PASS_PATH_CONDITIONED_READSET_SCOPED` requires exact 39-row coverage, two-or-more safe PATH_CERTIFICATE salvages versus GLOBAL_UNION, zero PATH_CERTIFICATE false accepts, all three audit mutations rejected, and an independently matching fixture/reason/certificate for every row. Any PATH_CERTIFICATE false accept is `FAIL_FALSE_ACCEPT`; zero safe salvage is `NO_ADVANTAGE`; missing/inconsistent provenance is `HOLD_DEPENDENCY_PROVENANCE`; mutation escape is `HOLD_AUDITOR_COVERAGE`. Comparator false accepts are reported, not hidden by the aggregate status.

**C.** A declared global union with complete instrumentation remains conservative and may be the safest operational rule when path proofs are unavailable. `EXECUTED_PATH` can look selective while silently missing a hidden read. Certificate construction and validation may cost more than recomputation. This fixture does not model that engineering overhead.

**U.** This is a finite authored model with complete/incomplete instrumentation labels, not evidence that a GUI, document, prompt, or model call has a complete read footprint. It grants no input authority and supports no GUI correctness, effect, runtime reliability, latency/token gain, portability, or product claim. Exact simulated field counts are not runtime cost measurements.

## Execution and freeze rules

- Candidate input is literal, in-memory synthetic data. The Python process has no network, model, GUI, application, or OS-observation calls. It writes only the exclusive-create candidate output file.
- The shared WSLc lane has an explicit unresolved owner-release gate in #7924/#8503. This T0 requires no container boundary and uses native Windows CPython 3.12.10 on the deterministic in-memory fixture. This is not a WSLc or Linux portability result. No WSLc/Docker query or operation is part of this allocation.
- Freeze `candidate.py`, `audit.py`, both construction tests, this protocol and base commit in `FREEZE.json` before formal candidate execution. Formal candidate runs once; the independent auditor runs once only after candidate exit 0 and output exists. Outputs use exclusive-create. No retry, post-freeze edit, or replacement is permitted.
- Construction tests do not count as formal candidate/auditor runs and are complete before freeze. If a frozen hash differs before formal execution, STOP without candidate. If candidate or auditor fails, preserve the first outcome and stop.

## Frozen commands

Construction suite (before freeze only):

    python -B -m unittest -v test_model.py test_audit.py

Formal candidate (once):

    python -B candidate.py --output results/candidate.json

Independent auditor (once, only after a successful candidate):

    python -B audit.py --candidate results/candidate.json --output results/audit.json
