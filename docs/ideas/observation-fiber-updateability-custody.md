# Observation-fiber updateability and allocation custody

- **Source:** Open [Issue #6774](https://github.com/Unjuno/agent-interface/issues/6774), a finite synthetic successor to [#5368](https://github.com/Unjuno/agent-interface/issues/5368).
- **PR-reported result:** merged [PR #6775](https://github.com/Unjuno/agent-interface/pull/6775) reports a nine-case Windows host-CPU run: candidate and raw-only audit agreed on 9/9 rows (`PASS_METHOD_SCOPED` / `PASS_READONLY`). The candidate admitted two invariant feasible controls, requested a distinguishing field on five mixed fibers, and rejected one impossible and one `UNKNOWN_MODEL` case. The baseline falsely admitted 7/9 cases in this declared fixture. This reports the retained outcome; current raw-byte custody is unresolved.
- **Current Issue disposition:** Open for post-closure allocation-collision custody. Do not treat its state as a new run request or the nine-case result as invalidated.

## Distinct execution disclosed after merge

After PR #6775 merged and Issue #6774 closed, a separate local execution was disclosed under the same allocation ID: 12 rows, candidate exit 0, auditor exit 0, and `FAIL_AUDIT` on the preregistered `ordered_field_ladder` hint. The disclosure explicitly calls this an accidental duplicate, not a valid successor or replacement for the nine-case result. A subsequent read-only check verified a ten-file manifest for that local packet, but could not uniquely attribute its executor; it therefore did not repair or promote the result. The Issue was reopened to preserve both histories and resolve custody.

The current repository package at `research/analysis/view_updateability_5368_t0/` contains nine-row candidate, baseline and audit files, but their current SHA-256 values do not match `RUN.json`: candidate `8d9195a9…` vs recorded `0286db0b…`, baseline `9e37ab24…` vs `327ef9b4…`, and audit `9529df83…` vs `c1012d41…` (full current hashes were checked directly on 2026-10-17). The source issue explicitly leaves the nine-row packet’s terminal-byte/source custody unresolved. The 12-row packet was inspected in a separate checkout and must remain a separate disclosed execution. Do not overwrite, pool, rerun, repair, or regrade either allocation. See the [reopen/custody comment](https://github.com/Unjuno/agent-interface/issues/6774#issuecomment-5959742178), [read-only packet check](https://github.com/Unjuno/agent-interface/issues/6774#issuecomment-5988381606), and [merged PR](https://github.com/Unjuno/agent-interface/pull/6775).

## Scope

The canonical result establishes exhaustive actionability only for its enumerated observation fibers and authored effect oracle. It does not establish complete GUI state coverage, natural ambiguity rates, live safety, model/human behavior, latency, or general view-updateability. The collision and custody gap are provenance issues; they do not convert the nine-case candidate outcome into a scientific failure.
