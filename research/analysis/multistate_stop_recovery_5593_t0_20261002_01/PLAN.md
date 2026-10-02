# Frozen experiment plan

Allocation `5593-MULTISTATE-STOP-RECOVERY-T0-20261002-01`; see `FREEZE.json` for immutable main, fixture, candidate, auditor, test and image identities.

## H/T/D/C/U

- **H:** SAFE_STOP can remain nonterminal while same-episode recovery proceeds; explicit states preserve repeated stop/recovery, final disposition, and administrative censoring without losing launched denominator mass.
- **T:** Candidate processes the five-episode frozen fixture once. Only after exit 0, a distinct raw-only auditor independently rebuilds every tick's occupancy and transition counts, validates paths, and executes the six frozen corruption controls. Each runs in a separate disposable, network-disabled pinned-image container. No retries.
- **D:** `PASS_METHOD_MULTISTATE_SCOPED` iff all occupancy rows sum to N=5 at every tick; candidate output exactly matches independent reconstruction; SAFE_STOP→RECOVERING, repeated recovery cycles, absorbing terminal states and CENSORED remain distinct; and all six corruption controls are rejected. Otherwise preserve FAIL/STOP as observed.
- **C:** A direct episode table may suffice; transition summaries add no decision value for many practical cohorts. The hand-authored fixture is deliberately small.
- **U:** Synthetic finite bookkeeping only. No empirical policy effect, causal recovery benefit, independent censoring, runtime behavior, or product safety claim.

## Container and I/O

Image ID is pinned in `FREEZE.json`; network disabled; 1 CPU, 256 MiB, 64 PIDs; fixture and code read-only. Candidate and auditor run in separate fresh containers. No existing container is entered, stopped, or changed.

## Retained construction issue

The first construction-suite invocation exposed one incorrect test expectation: tick 3 also contains the independent direct-success transition. The assertion was corrected before freeze; the final 11-test suite passed. This construction correction is not a formal candidate/auditor retry.
