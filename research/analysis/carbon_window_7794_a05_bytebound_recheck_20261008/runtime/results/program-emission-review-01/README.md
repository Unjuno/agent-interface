# Explicit per-program emissions in public review outcomes

The actual four-case Inkscape comparison initially added X11 cumulative counters10+14 and reported24 emissions for a two-program case; its immutable first audit and correction are retained in `inkscape-conditional-live-01`. The correct program deltas are10+4=14. Public `outcome_summary` exposed a top-level refusal counter but omitted the nested execute counter, so a caller had to inspect the full raw receipt to find the program-scoped value.

`runtime.cli_v1.review.outcome_summary` now exposes `program_emissions` from `result.execution.program_emissions` as well as the existing `result.program_emissions`. An explicitly reported strict nonnegative integer is preserved. If both copies exist, both must be valid and equal; disagreement or a malformed copy gives null. A missing counter remains absent. `execution.emissions` is never substituted and missing evidence never becomes0. Raw reports, source hashes, counters, execution, image choice and success/recovery/release handling stay unchanged. Full/compact/brief/summary routes retain the same outcome object. No input, capture, source renewal, replay or task-success inference is added.

For the X11 backend, `execution.emissions` is cumulative for the backend connection, while `execution.program_emissions` is the delta during that execute invocation, including cleanup emissions during it. Neither measures the number of semantic actions. Events outside the invocation, such as a later owner close, need their own receipts. A reported0 alone never proves no input, neutral release or task completion. This is descriptive retained evidence, not an independently attested physical event count. Other backend semantics cannot be inferred merely from an unrelated `emissions` field.

## Actual retained input and packaged recheck

The prior positive ordinary Inkscape draw/Save receipts were read from exact Git bytes and reviewed with the current CLI and expected raw SHA256. CLI reviews emitted no new images or input. Counters were:

| Program | Raw backend cumulative emissions | New public outcome program emissions |
| --- | ---: | ---: |
| draw | 10 | 10 |
| Save | 14 | 4 |

The sum is14. Original complete wrappers are identified by source path/hash in `retained-recheck.json`; retained raw extraction has its own hash. No historical file was changed or scientific comparison rerun. Both reports have no inline observations, so this check does not establish image delivery behavior in a fresh GUI. The same exact two raw reports were reviewed from a source-pinned portable `runtime.pyz` under Python-I from an outside-repository directory without PYTHONPATH. Both returned10/4. Archive and manifest/hash/command/stdout/stderr/exit evidence are retained under `archive-check/`.

## Validation and failures

Four regression tests first reproduced missing successful-program counters and conflicting top/nested evidence (red exit1); then the implementation made them pass. Controls cover cumulative10→14 versus delta10+4, no fallback from cumulative0/14, missing fields, explicit execution-failure0 without a no-input inference, booleans/strings/floats/negatives/null, contradictory/agreeing copies and old refusal0, full/compact/report-ref byte identity, and image-presentation fallback preserving raw results. Related38 tests passed normally and-O. Full committed-source native check:401protocol/192harness PASS; complete logs and SHA references retained/independently checked. Source code commit `935fb5aba0f82ff3ee912aee9e0b172c9a626c7f` is pinned before the native/archive runs.

The first manual retained-case read attempted a sparse worktree path that was not materialized. It failed before a CLI recheck; exact HEAD Git bytes were read instead and the failure is recorded in `preparation.json`. No native input or observation was invoked.

This production presentation fix avoids repeating an observed accounting mistake; it supplies no matched model speed, token, cost, human-tempo or generic task-performance claim. Previous image/summary efficiencyHOLD and the broad goal remain open.
