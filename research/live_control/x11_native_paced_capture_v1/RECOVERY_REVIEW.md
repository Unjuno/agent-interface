# Recovery review: Issues #3949 and #3965

This recovery preserves the two `SOURCE_FREEZE.md` records from the
2026-09-22 branch. The branch contained only these freeze notes; the 32-file
v1 source archive described by its note, formal raw data, and v2 batch results
were not present. A bounded search of accessible `/tmp` and Codex workspace
file paths found no matching local bundle.

## v1 allocation — Issue #3949

Issue [#3949](https://github.com/Unjuno/agent-interface/issues/3949),
comment [5766363408](https://github.com/Unjuno/agent-interface/issues/3949#issuecomment-5766363408),
records `STOP_EXTERNAL_EXECUTION_ENVELOPE`: the single frozen 40-case run
reached 30 acknowledged rows, with one additional child-side case not
acknowledged by the orchestrator. Cases 31–39 were not started. The terminal
runner exit/hash receipt is missing, so the 30/40 partial counts are descriptive
only; there is no full-denominator scientific verdict. The Issue reports raw
and checkpoint hashes, but the corresponding bytes are absent from this
branch and local search. Do not promote the child-side case to row 31 or
resume/pool this allocation.

## v2 allocation — Issue #3965

Issue [#3965](https://github.com/Unjuno/agent-interface/issues/3965) classifies
the five-batch plan as an execution record under #3949, not a new scientific
question. Its available comment records a preformal freeze and zero formal
cases at that point. No later formal outcome, batch receipts, or raw output
were found in the accessible Issue comments, old branch, or bounded local
search. This is an evidence-availability statement, not proof that no local
execution ever occurred. Do not start or complete the five batches from this
recovery; preserve the consumed-v1 STOP and the v2 freeze separately.

## Boundary

The freeze notes are recovered verbatim. No X11 allocation, batch, retry,
replacement, or GUI/model/input action was run. The v1 source bundle and both
formal output packages remain unavailable here, so this PR is provenance
recovery only, not a result report or runtime recommendation. Any later
evidence found should be audited from its saved bytes under the existing Issues,
without rewriting these predecessor records.
