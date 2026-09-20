# Primary continuation use: terminal compatibility failure retained

The primary assistant started one private Inkscape allocation and observed its
image. The first startup wait returned starting; a second wait reused owner
18752 and returned ready. After six right chords, the response supplied stage 2,
source_sequence 7 and the exact source-2 hash. The assistant viewed that image
and used those numbers for a second keyboard action: twelve right chords, save,
finish_after=true. Both input actions completed and final pixels showed x=86.

The allocation did **not** finish successfully. The current harness no longer
processes finish_after, so it published a boundary for stage 2 and raised
`bounded action stages exhausted without explicit finish`. Continuation correctly
returned needs_review/stage_bound_exhausted. Owner exited 1, task evaluation is
absent, cleanup reported completed, and EOF closed relay exec 59769 with code 0.
Saved SVG x=86 is an independent observed effect, not proof of task completion.

Source inspection found the harness's latest change was bdef92411 (#3417,
"Rescue native terminal cleanup evidence v2"). That source retains explicit
finish but lacks finish_after handling, while the MCP schema still accepts it.
This is a compatibility gap to resolve; do not restore code blindly or claim
successful completion from the saved image. Preserve this run without replay.

PLAN.md precedes allocation; full responses, original images, exact requests,
cleanup/error files, harness snapshot and source/exit provenance are retained.
manifest.json hashes the original archive entries and predates this README.
The archive check verified that the second request uses the supplied continuation,
its source hash matches, evaluation is absent and cleanup completed. No independent
full auditor or container experiment was run for this new trial. No speed/error-rate
benefit is established. The live result is FAILED_TERMINAL_COMPATIBILITY, with
scoped evidence that the descriptive continuation was consumed by the primary.
