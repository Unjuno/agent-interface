# #5265: retained construction evidence and comparator boundary

This additive record preserves previously executed construction, not a new experiment.
Dedicated GitHub-hosted experiments were cancelled. No simulation, formal run, or
runtime change was performed for this publication. Prospective formal_v1/v2/v3 drafts,
workflows and launch sentinels are excluded and must not be run from this record.
The frozen PLAN and runner are historical evidence, not current execution authority.

## Useful result preserved

Allocation `DOT-5265-CONSTRUCTION-20260930-01` ran one construction matrix:
49 traces / 196 arm rows, comprising 47 shared-ID primary traces and two
missing-common-ID boundary traces. The freeze followed construction; formal invocations: 0.

| Modeled policy | Primary duplicates | Primary missing valid effects |
|---|---:|---:|
| Producer-local retry only | 14 | 0 |
| Content-bound common semantic work ID | 0 | 0 |
| One effect per session/generation | 0 | 11 |
| Exact semantic tuple coalescing | 0 | 0 |

All primary unauthorized-effect, cross-goal-merge and oracle-error counts were 0.
When the common ID was absent, the common-ID policy conservatively yielded in both
boundary traces, leaving two goals unfulfilled; tuple coalescing preserved both.

The resulting interpretation is **conditional redundancy**: once the shared semantic
work identity is already available, a #24-style content-bound ledger can match the
coalescer in this finite model. This does not show that real independent producers
can obtain that shared identity, or establish sufficiency of the integrated #24/#732
runtime. Likewise, the 11 missed effects refute only this one-effect-per-generation
policy; they do not refute single-writer serialization generally.

## Relationship to merged PR #5338

Read via GitHub MCP at merge commit
`ff93fdb5b6b1740d85a79e79764e9dc7789831fe`. The merged experiment/workload/plan hashes
match its own FREEZE; source links and hashes are in MERGED_COMPARISON.json.

[The merged result](https://github.com/Unjuno/agent-interface/blob/ff93fdb5b6b1740d85a79e79764e9dc7789831fe/research/experiments/action_effect_coalescing_5265_v1/RESULT.md)
reports a scoped synthetic T0 PASS: two policies across ten cases, reducing the
identical cross-producer pair from two effects to one. It explicitly leaves
#24/#732 composition sufficiency unresolved. Our retained construction contributes
the stronger common-work-ID comparison and the constrained scheduler's liveness
counterexample. Counts must not be pooled across these different contracts.

A concrete contract difference deserves preservation rather than verdict rewriting:
- Merged `experiment.py` includes `deadline_ms` in semantic identity. Its
  `same_effect_different_expiry` workload explicitly expects two effects from both
  policies when only expiry changes. It also expires at `now >= deadline`.
- Our frozen semantic tuple excludes deadline, while each proposal separately passes
  its own deadline admission; expiry is `now > deadline`, so equality remains valid.
  Our matrix did **not** execute a pair differing only in deadline. The identity-key
  difference is source inspection, not a new empirical result or a failing test of
  the merged study.

Thus the merged scoped PASS and this conditional construction HOLD answer different
questions and coexist. Neither establishes that a new runtime abstraction is needed.
No previous result or decision is changed by this publication.

## Integrity, limits and provenance

The exact 28-file frozen closure is retained unchanged with FREEZE.json:
`b3e80a1c4a8acd3841f6df61b6e69986343ca664c5bb15089a00d0b36805d426`.
Raw SHA256: `f35228e59c73219fe4c42437a7ac5f0ff9ffd0a87d692610c8588a3bf2d056cc`.
Previously executed independent-implementation audit: 196 rows, no errors; copied-output
corruption controls rejected 6/6. Original stdout, stderr and red/green checks remain.
This publication preparation only rechecked file hashes and inspected merged source;
it did not rerun those experiments or relabel construction as formal evidence.

Preserved caveats:
- `same_attempt_different_session` actually uses different attempt IDs; identical-
  attempt cross-session rejection was not covered by this construction.
- This is atomic, in-memory finite logic with hand-authored goal labels, not real
  concurrent workers, a durable ledger, live GUI authority or physical cleanup.
- Python's original platform.platform() receipt may spawn a short uname subprocess;
  the old strict no-child-process wording is overstated. No performance claim follows.
- Five upstream reference copies have one added trailing LF; SOURCE_PROVENANCE
  records that removing exactly that LF reproduces their original Git blob hashes.
- Original local STOP_CONTAINER_RUNTIME_UNAVAILABLE_NO_PROMOTION is historical
  setup evidence, not a fleet-wide statement or the merged study's disposition.

SALVAGE_MANIFEST.json describes exactly this publication set. It excludes unrun
prospective allocations and contains no workflow or automatic experiment trigger.
