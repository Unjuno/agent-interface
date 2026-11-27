# PR #8169 / Issue #7804 evidence correction — 2026-11-22

Read-only current-main recheck at `2a5086596b12b781bd42c0c0ea8ef8dd39ce58c8`.
The linked [Draft PR #8169](https://github.com/Unjuno/agent-interface/pull/8169)
is still open and retains a 40-file, 86,718-addition packet for
[Issue #7804](https://github.com/Unjuno/agent-interface/issues/7804).
Its candidate ran once and exited 0; the independent auditor process did not
start (`exit 125`, process invocations 0); retries were 0. The correct
allocation disposition remains `STOP_INFRA_AUDITOR_LAUNCH`, with no scientific
PASS/FAIL and no rerun.

## Self-review findings reconciled against retained files

1. The two preflight `run_metadata.json` files contain opposite-role boolean
   fields set to `false`. In each role, the corresponding applicable isolation
   booleans are `true`, and the exact-allowlist probe stdout records the role's
   source allowlist, read-only source, and separate output checks as passing.
   Treat each cross-role field as **not applicable**, not as observed leakage.
   Preserve the original metadata bytes; the addendum supplies the role
   interpretation.
2. `results/a01/auditor.stderr.txt` says Docker rejected
   `research/analysis/quotient_first_exploration_7804_t0_a01_20261005/results/a01/candidate.raw.json`
   as an invalid **mount path** because it was not absolute. By contrast,
   `results/a01/run_metadata.json` attributes the problem to a relative bind
   **source**. Its `auditor.command` is prose, not exact argv or a source/target
   tuple. The saved records establish auditor launch failure, but do not
   establish whether that relative string was the host source or container
   destination. The source-versus-target cause is unresolved; do not repeat the
     metadata's unsupported source-specific explanation as fact.

The retained candidate raw SHA-256 is
`92ccdd61d166decc8ffd022f7811967379dcd674ad40f29d7d3199439d4d3572`; the
auditor stderr SHA-256 is
`f7dafa47cb2c3dd91dbac75d27245ba858afd35580a9b166d81098dcbb511e01`.

The candidate-reported 312 named states, 166 quotient classes, and transition
counts remain unaudited. Do not treat them as a method result or efficiency
gain. The predecessor integrity audit and construction/preflight checks are
separate scoped evidence; none substitutes for the missing formal auditor.

The raw STOP packet remains on the open Draft branch. Preserve it until its
unique evidence is either transferred byte-for-byte to a current-main successor
or the branch's custody and disposition are otherwise resolved. No container,
candidate, auditor, allocation, or WSLc command was run for this recheck.
