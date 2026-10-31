# Issue #59 PR-7692 release-order map — A04 composed boundary test

## Question and H/T/D/C/U

**H.** Connecting a candidate per-actuation map at the exact V19 capture seam to the exact V19 tail finalizer and V3 scorer adapter accepts all actual-schema key-pair boundaries under the finite 1–3 key schedules, while the frozen single-slot capture safely censors mismatches.

**T.** AST-execute exact `_capture_backend` and `_run_measured_tail` from PR #7692 V19; load the actual V3 adapter and its pinned V1 scheduler dependencies; feed all 41 admission/release permutations cloned from the retained producer event shape to both exact single-slot and candidate-map capture factories; invoke `MainThreadScorerStdin.sample_measured_tail` with zero duration; audit every pair and event boundary independently.

**D.** `PASS_COMPOSED_BOUNDARY_CANDIDATE` iff the exact single-slot accepts 15/41 identity boundaries, candidate map accepts 41/41, all schedules end with empty held state, all calls remain controller-invisible and non-authoritative, and all zero-duration calls take zero samples while finalization runs.

**C.** The original scorer-tail feature is optional and may be unnecessary if overlapping holds do not occur in authorized runtime traces. A measured boundary only matters if it supports a scientifically useful endpoint.

**U.** This executes exact V19 capture/finalizer functions and the exact V3 scorer adapter, but the V19 main/session is not run. It uses the captured producer schema with synthetic identifiers/timestamps, socketpair-backed scorer stdin, zero sampling duration, and no X server, physical input, controller, GUI, model, game, or live allocation. PR #7692 remains an unmerged, older-base draft. No main runtime behavior is changed or qualified.

## Result

The exact single-slot path accepted 1/1, 2/4, and 12/36 boundaries (15/41); all 26 identity mismatches were classified `no_matched_release_pair` / `MeasuredReleaseError`, with finalization still called. The candidate nested-identity map accepted 1/1, 4/4, and 36/36 (41/41). Every accepted zero-duration tail was `CENSORED` with `termination=deadline`, `tail_samples=0`, `controller_visible=false`, and `grants_input_authority=false`. Independent audit passes all 82 schedules and source/event pins.

This adds composition evidence beyond a standalone candidate wrapper, but does not establish how often overlapping holds occur or whether scorer-tail measurements improve computer control. A live threat exposure remains separately unavailable while the private game lane is unassigned.

## Reproduction

Python 3.10+:

```powershell
python run_composition.py
python verify.py
python -m py_compile run_candidate.py run_composition.py verify.py
```

`SHA256SUMS.txt` lists the retained scripts, exact source dependencies and producer rows.

## Addendum: evidence lineage

A02's original PASS_CANDIDATE was a synthetic wrapper result and used a root-level actuation identity. The producer-schema correction and raw event-shape check are retained in sibling a03/; A04 composes the exact V19 backend capture seam with the exact V19 tail finalizer and exact V3 scorer adapter. The source PR remains unmerged and is not current-main runtime evidence.
