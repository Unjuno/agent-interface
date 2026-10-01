# Self-action history invalidates stale Inkscape selection guard

Task `INKSCAPE-ACTION-HISTORY-INVALIDATION-20260916-001`, Issue #475.

## Decision

**`PASS_SELF_ACTION_HISTORY_INVALIDATION_SCOPED`** for completed allocation `inkscape-action-history-invalidation-20260916-a2`.

A1 is separately retained as `INCOMPLETE_SUPERVISION_TIMEOUT`: seven complete rows, one partial row and eight unstarted rows. It was not resumed and contributes no row to A2.

## Question

Retained #327 showed a real Inkscape boundary: after A was visibly revalidated, the controller could emit `Tab`, semantic selection could become B, and 120 ms later the unchanged A-handle pixel guard still reported the same positive pixels. Ordinary Right input then moved B.

This experiment leaves that pixel guard unchanged. It changes one factor only: whether a relevant self-authored selection-navigation receipt occurring after A revalidation invalidates the old target-sensitive authority.

The candidate does not infer that Tab selected B. It only says the earlier A observation is no longer sufficient authority after a relevant self-authored action.

## Formal result

A2 used 16 fresh cases, four per stratum. The exact scientific row order from A1 was preserved; only outer supervision changed so each four-case chunk ran in its own invocation.

| Context | Policy | Actual first outcomes |
|---|---|---:|
| stable | current guard only | 4/4 ADMIT, A +10 / B 0 |
| stable | history invalidate | 4/4 ADMIT, A +10 / B 0 |
| self-switch | current guard only | 4/4 ADMIT, A 0 / B +10 wrong target |
| self-switch | history invalidate | 4/4 `STOP_HISTORY_INVALIDATED`, zero Right effect, A 0 / B 0 |

Every one of the 16 final guard captures remained positive with exactly top/right/bottom = 64/176/64 and RGB SHA-256 `45f96568c969d5fb1ff04769a469d45ecc79c27849da4e43dc9cd48e1abd6ee5`. Thus the candidate difference is not a fresher or better screenshot.

Every self-switch row has exactly one `selection_navigation` / `Tab` receipt ordered `revalidation_end < receipt.start <= receipt.end < guard_start`. Stable rows have zero relevant receipts. All relevant keys and mouse buttons are empty at terminal in 16/16 cases.

The frozen independent auditor recomputed guard pixels, final A/B geometry, receipt ordering, policy/stratum outcome, release state and frozen source identities. Decision PASS, errors 0; audit SHA-256 `8db549b46c52487030cb68b431015c96220792f81ff4d91f0feaed3b86414cb2`.

Five postformal mutations applied only to copied evidence/source were rejected 5/5: decision claim, receipt ordering, guard pixel, saved-SVG effect and runner source bytes.

## Interpretation

A relevant self-authored action can act as **negative authority evidence** even when the resulting semantic state is not directly observable quickly enough. In this scoped race, remembering that the controller itself navigated selection after A revalidation prevents stale A authorization from being reused against an aliased visual guard.

This is deliberately weaker than semantic identity. The receipt proves that an authority-invalidating action was attempted; it does not prove which object became selected. The safe response is refusal/re-observation, not positive authorization of B.

## Retention boundary

GitHub retains exact frozen source/preregistration, A1 interruption metadata, the completed A2 aggregate result, all 16 claim-relevant receipt/timestamp/effect rows, the exact three final-SVG terminal-state exemplars, audit/control summaries, and exact SHA-256 identities for claim-relevant screenshots/results.

The full A2 local result tree is 133 files / 5,062,870 bytes. Its canonical path/hash/size manifest digest is `8fbe4b310711d6c859fe360a3109cb766891c5d8345697439cf19d2fd7ac1c20`. The full screenshot bytes are **not** embedded in GitHub. The common guard ROI PNG is identified by file SHA-256 `00b31be761ac7ab7be9a1ec6f28ee962573de535154830fe6c1e33ce54c33aad` and decoded-RGB SHA-256 `45f96568c969d5fb1ff04769a469d45ecc79c27849da4e43dc9cd48e1abd6ee5`, but its image bytes are not claimed GitHub-retained. Two attempted image-publication objects had Git-object mismatches and remain unreferenced; they are explicitly not evidence.

## Limits

The mechanism covers only relevant actions authored by this controller. It does not detect a user, another process, an application-internal change or an uninstrumented path. A Tab can fail to change selection, so the rule can conservatively reject a still-valid A state; this experiment does not estimate that false-stop cost.

One Inkscape 1.4/X11 fixture, one target-sensitive key effect and one authored 120 ms paint-lag interval only. No AT-SPI identity, application-owned atomic commit, natural race frequency, speed, model benefit or production claim.

## Next single question

Hold self-action invalidation fixed and add exactly one **external/unreceipted** post-revalidation selection change. The expected boundary is that self-action history alone cannot invalidate it; a separately measured semantic source would be needed. Do not generalize this receipt into external-change detection.

## ERROR CHECK

A2 contains 16 distinct IDs, four per stratum, and no A1 row. Each A2 chunk completed once with return code zero. The four expected terminal-effect strata are exact 4/4, the guard RGB/counts are identical 16/16, release is empty 16/16, and the frozen auditor reports zero errors. No A2 measured ID was rerun or replaced.
