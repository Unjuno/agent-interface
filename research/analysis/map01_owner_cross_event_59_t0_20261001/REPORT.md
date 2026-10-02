# Issue #59 — cross-event live-04 owner-guard counterexample

**Disposition: `FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER`.** The exact frozen helper admitted both event-partitioned rows; the independent oracle found two admissions for one versioned workflow path/allocation. This is a deterministic synthetic source-composition counterexample, not a live experiment or claim that a duplicate workflow run occurred.

## Question

Does live-04's allocation-global guard composition enforce at most one formal entry across all events for the versioned workflow path, or only within the current GitHub event type?

The workflow supports both `push` and `workflow_dispatch`, and its run-list URL includes `event=$GITHUB_EVENT_NAME`. The helper then selects the earliest matching workflow-path run from only the rows it receives. A deterministic composition counterexample is preregistered in `PLAN.md` and represented by one real push-run anchor plus a clearly marked synthetic dispatch row.

## Scope boundary

This is an offline deterministic source-composition test. The synthetic dispatch row is not evidence that a second workflow run occurred. The retained live-04 result remains a scoped `PASS_MEASUREMENT_INTEGRATION`; this audit asks whether its source guard's allocation-global claim covers the declared dispatch trigger as well as push.

No Actions dispatch, game/model/GUI/input, Docker/OrbStack container, GPU, or network operation is part of the candidate/audit. The exact source freeze, H/T/D/C/U, decision rule, and repair boundary are in `PLAN.md`; operational details are in `RUN.md`.

Adjacent open PR #5948 studies a separate owner-guard input-integrity axis (duplicate rows hiding distinct runs); it touches neither this additive package path nor the live-04 workflow/helper. This T0 holds the run set fixed and isolates the event-filter partition, so the two tests are complementary rather than duplicates.

## Result

The frozen candidate returned `PASS_CANONICAL_GLOBAL_OWNER` for both the actual push-run anchor and the synthetic dispatch row because each event-filtered payload contained only its own current run. The independent audit returned `FAIL_EVENT_FILTER_ESCAPES_PATH_GLOBAL_OWNER` (`admitted_count=2`; admitted IDs `34971205791` and synthetic `90000000001`). Exact invocation outcomes, hashes, and the malformed initial auditor CLI invocation are retained in `RUN.md` and `audit.json`.

Conclusion: the current source composition does not demonstrate at-most-one entry across every declared trigger; its helper-global selection is only as broad as the event-filtered payload supplied to it. A successor should independently test or repair the path-global policy in a new additive, versioned workflow/path. Do not rewrite the live-04 record based on this synthetic result, dispatch workflows to prove the construction, or merge a guard repair into the historical implementation. This result does not establish real concurrency behavior, runner scheduling semantics, or MAP01 task efficacy.
