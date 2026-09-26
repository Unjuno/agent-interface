# Typed negative-outcome contract — Issue #4174

## Disposition

**HOLD_EVIDENCE_INCOMPLETE_AFTER_CONTAINER_RESET**

The single preregistered formal invocation completed 144/144 rows and exited 0. Formal reruns/replacements/tuning were 0/0/0. The retained RAW SHA-256 recorded immediately after execution is:

`0e6b99fe110d2958cbc960b6660d928c121ee6129dd01bada05a46d7e40cff69`

The frozen auditor then exited 1. Its semantic reconstruction reported no candidate-row errors, but the preregistered corruption-control gate failed because 2/12 mutations escaped:

1. `stale_to_current` was a no-op on the selected already-CURRENT row.
2. `row_id` changed one ID to a still-unique value; the frozen auditor checked count/uniqueness but not the exact r000..r143 set.

The audit failure is retained and is not rewritten as PASS.

After this outcome had been recorded on GitHub, the execution container was reinitialized and the original RAW/AUDIT files were no longer mounted. The exact RAW bytes therefore cannot be committed from this continuation. They are not regenerated from the frozen source because `run.py` records wall-clock timestamps, so a rerun would create different bytes and would violate the no-rerun rule.

A postformal read-only audit-v2 had been attempted in the prior execution context, but its original output/receipt bytes are also unavailable after reinitialization. It is therefore not used to qualify this PR.

## H / T / D / C / U

**H.** Evidence-backed typed outcomes should preserve UNKNOWN and bounded retry guidance; a coarse status/timeout comparator should expose futile-retry and premature-terminal counterexamples.

**T.** Frozen corpus: 9 families x 2 freshness states x 2 completeness states x 2 retry contexts x 2 repetitions = 144 rows. One formal invocation only. Standard library; no GUI/model/provider/network/input.

**D.** PASS required complete 144-row execution plus an independent audit with errors=[] and at least 10 coherent mutation controls rejected. The formal runner completed, but the frozen audit gate did not pass. Therefore the preregistered PASS is not awarded.

**C.** Authored finite contract fixture. The coarse comparator is deliberately incomplete and is not alleged to be production behavior.

**U.** Real application evidence extraction, planner/model comprehension, task quality, tokens, latency, cross-domain generality and production integration remain untested.

## Chronology

- Issue #4174 created after collision searches.
- Initial proposed branch name collided with unrelated #2494 history; no #4174 file was written there.
- Corrected branch `research/typed-negative-outcome-4174-20260923-v1` created from `b38806cd09243f7ad18deb61db44048bc3feffae`.
- Exact source/gates were published before formal execution; branch head at freeze `e8b4e9c2644a4eac560c08f24e30c40c255c9b12`.
- Construction: four unit tests plus excluded 12-row smoke passed.
- Formal: 144/144 rows, exit 0, reruns 0.
- Frozen audit: exit 1 because two corruption controls failed to reject.
- Container reinitialization later removed local formal bytes; no scientific rerun was performed.

## Scope

This PR preserves source, preregistration and the exact failure/HOLD record. It does not claim repository-byte-complete formal evidence, scientific PASS, planner benefit, runtime promotion or closure of parent #39.
