# Dependency-scoped continuation during unresolved effects

**Canonical question:** [Issue #93](https://github.com/Unjuno/agent-interface/issues/93) asks when an agent may continue independent work while an application effect has not yet been resolved. The useful boundary is exact dependency evidence and a separate effect owner: unrelated work may progress, while dependent or uncertain work stays blocked. Elapsed time, a missing acknowledgement, or a guessed resource footprint cannot prove that an effect did not occur.

## Retained evidence

| Record | What it establishes | Limit |
|---|---|---|
| [PR #98](https://github.com/Unjuno/agent-interface/pull/98), merged as `f78937970b3d14ec4698383a3e875205d4fc6327` | 75 frozen native Tk/Xvfb/Openbox/XTEST cases compared five policies across five scenarios and three repetitions. The canonical frontier had 9/15 exact complete workflows and zero incorrect dependent outputs; adding read-only status lookup had 12/15 and zero incorrect outputs. Release-only continuation produced 15/15 incorrect dependent outputs. Six equal-correctness pairs measured a 204.276 ms median paired reduction for the canonical frontier versus global wait. | A fixture-scoped result with deliberately injected delays, not general agent speedup, Agent Interface runtime integration, Doom/MAP01 efficacy, or live desktop authority. Unknown and dropped effects remain unresolved. The 672,186-byte full raw archive was delivered outside GitHub; the digest is `39db3b61550681633a22de0eda687a63446d0dbbdf2bf611dee7d3a169f81530`. The 30 gate tests are reproducible from the repository; full raw replay and nine audit-mutation tests require that archive. |
| [Issue #165](https://github.com/Unjuno/agent-interface/issues/165), closed discovery successor from #93 | Flat resource IDs miss alias remaps and query phantoms. Typed READ/RESOLVE/QUERY/WRITE evidence distinguishes those dependencies; global epochs can safely reject unrelated work. | Finite Git/SQLite mechanism checks do not provide a live GUI dependency contract or effect-safety result. |
| [PR #162](https://github.com/Unjuno/agent-interface/pull/162) and [PR #158](https://github.com/Unjuno/agent-interface/pull/158) | Under a fixed atomic Git effect boundary, omitted dependencies allowed stale effects while exact dependencies rejected stale changes and permitted unrelated progress. A multi-ref transaction avoided partial writes that sequential CAS allowed. | Git-specific atomicity and authored predicates do not establish complete footprints for an arbitrary application. |

## Current disposition

Keep #93 open. Its candidate has a useful finite result, but the parent asks a broader application question and the current caller does not consume complete typed dependency evidence for live effects. Preserve the distinction between safe continuation and task success: neither a resolved dependency nor an empty status response authorizes replay of an old input. Continue the computer-control supervisor work on its own gates; this family does not replace fresh-target recovery, independent task-effect verification, or the release boundary.

## Smallest useful next test

If a local caller integration is selected, compose one pending effect with (1) one independently verifiable operation, (2) one alias remap, (3) one query-membership phantom, and (4) one unknown footprint. Require an independent oracle to reject stale dependent work, allow only the proven-independent operation, and retain UNKNOWN for unresolved effects. Measure correctness and completion time on equal-correctness pairs. Keep it local/Fake X until the typed dependency contract survives those cases; do not consume WSLc, add a shared-runtime default, or reuse the completed #98 result as a new allocation.
