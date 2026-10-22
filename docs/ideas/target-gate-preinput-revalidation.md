# Target-gate pre-input revalidation — one scoped rung from Issue #105

This crosswalk records only the pre-input patch-revalidation result. It is not
a complete disposition of the long-running discovery ladder in
[Issue #105](https://github.com/Unjuno/agent-interface/issues/105), which stays
open as the coordination record.

## Evidence lineage

- [#956](https://github.com/Unjuno/agent-interface/issues/956) rejected a
  local pixel-patch gate as semantic identity: an ID-only object swap preserved
  the rendered pixels and a zero-error patch match while changing the semantic
  object under the point in all four cases. The gate cannot infer identity
  absent a separate current-evidence relation.
- [#965](https://github.com/Unjuno/agent-interface/issues/965) exposed a
  post-gate visible target/decoy swap. Its original first block stopped after
  9/12 cases; [#969](https://github.com/Unjuno/agent-interface/issues/969)
  completed a fresh 12-case successor. The provenance audit in
  `research/live_control/target_gate_provenance_reconciliation_v1/REPORT.md`
  shows that #969's bytes and case IDs are not identical to the separate
  current-main result retained by merged [PR #968](https://github.com/Unjuno/agent-interface/pull/968).
  Keep those two result lineages separate.
- Closed [Issue #972](https://github.com/Unjuno/agent-interface/issues/972)
  and merged [PR #975](https://github.com/Unjuno/agent-interface/pull/975)
  tested one additional mechanism against the #968/current-main gate: exactly
  one current screenshot immediately before pointer input, with the same
  radius-5, 11×11, max-RGB-error-8 patch check. Across 16 fresh private
  Xvfb/Tk sessions, stable cases clicked the task target 4/4 with and without
  revalidation; visible swaps clicked the decoy 4/4 without it and stopped
  4/4 as `STALE_TARGET` with zero task clicks after it. All terminal buttons
  were up.

## What the result does and does not establish

The added capture had median duration 1.586 ms; stable revalidation-complete
to click-start remained 5.192 ms median. This closes the synchronized visible
swap in that fixture. It is not an atomic observation/input transaction, a
semantic-identity check, or a shared-runtime integration. The smaller race
after capture and the pixel-identical alias from #956 remain. Raw PNG bytes
were not Git-retained; compact case/effect records, source hashes and the
independent audit are retained under
`research/live_control/target_gate_preinput_revalidation_v1/`.

## Disposition and next rung

Keep #105 open. #972/#975 is an adjacent completed TOCTOU rung, not completion
of the full discovery ladder and not a result for real gameplay. The
coordination Issue's Rung 1 remains the matched owner-deadline-expiry versus
explicit-cancel comparison on a real ViZDoom/X11 fixture with nonzero health
change. Do not infer this comparison from the separate expiry and two-dispatch
records. No new run or allocation was started for this crosswalk; first verify
the exact available host/allocation and preserve the existing STOP/HOLD on
shared WSLc ownership.
