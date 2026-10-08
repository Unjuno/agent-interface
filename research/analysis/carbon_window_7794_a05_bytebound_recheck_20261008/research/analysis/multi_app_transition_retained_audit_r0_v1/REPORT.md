# Retained multi-app transition integration audit — R0

Issue #1690.

## Decision

**PASS_RETAINED_MULTI_APP_COMPONENTS_NOT_INTEGRATED_SCOPED**

The frozen retained ledger contains evidence for every requested transition family, but not one session containing all four under a single integrated contract.

| Retained source | App | focus drift | modal | geometry drift | window replacement |
|---|---|---:|---:|---:|---:|
| PHASED_FOCUS | Inkscape | yes | no | no | no |
| SHARED_PHASED_CALC | Calc | no* | yes | no | no |
| GHD real-app report | Chromium | no | no | yes | yes |

*Calc's modal dialog causes expected focus transitions, but the audit deliberately does not relabel that as the external-focus-drift condition tested by PHASED_FOCUS.

Coverage union: all four families. Apps represented: Calc, Chromium, Inkscape. Same-session all-four rows: **0**.

The Chromium GHD evidence is important: geometry drift and real browser/window replacement already compose in one session. This audit does not fragment that evidence merely to make the gap look larger.

## Source/status evidence

Frozen `RESEARCH.md` still lists "Longer mixed-app sessions with app restarts, focus drift, geometry drift, and modal transitions" as future work. Bounded Issue/branch/code search found no exact integrated owner before #1690, but search absence is supporting evidence only and is not treated as proof about private, deleted or unpushed state.

## Integrity

Exact remote Git blobs were reconstructed locally before formal1:
- SOURCE_MAP `93248a6997ec2113e35667b853769913d0a9f708`
- LEDGER `e0f225f45c74eb7824dc710ac51d29bb010874e1`
- formal `cefebeeb0858152a3bb4d6fcad4487d37c12fb1c`
- audit `f386292ae1341287116f8e8de8991a7f3d445374`

One preformal analysis used a compact JSON serialization whose semantic content matched the frozen ledger but whose Git blob did not. It was rejected before formal classification. No scientific input or gate changed.

Formal1/reruns0/replacements0/tuning0. Independent audit PASS/errors[]; corruption controls6/6.

## Consequence

The ROADMAP item must remain open. Component PASSes do not establish the longer mixed-app integration claim.

A next empirical rung should be finite, not an unbounded endurance run. A high-information design should preserve one caller/controller identity across at least two desktop apps and schedule perturbations so that focus drift, geometry change, window replacement/restart, and a modal transition all occur with:
- independent task correctness;
- no wrong-target input;
- explicit refusal/recovery;
- verified release;
- transition timestamps and lineage;
- failed episodes retained.

This retained audit does not itself authorize or claim that live allocation.
