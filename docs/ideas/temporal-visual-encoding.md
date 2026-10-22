# Temporal visual encoding: history versus packing

This family preserves the idea from [Issue #1525](https://github.com/Unjuno/agent-interface/issues/1525) without treating its implementation, retained-data audit, and fresh prediction comparison as the same result. Live Issue states and comments were read at 2026-10-19 08:53 UTC.

## Distinct questions and retained outcomes

- **#1525 — temporal history as a spatial visual sheet.** The idea is to arrange time-ordered frames in one image for a multimodal model. The primitive is already used in retained DOOM runs as `temporal-sheet.png`; this establishes implementation/use, not that a sheet improves prediction. The original proposal explicitly made no superiority claim.
- **[#1550](https://github.com/Unjuno/agent-interface/issues/1550) — can retained results identify a packing effect?** Closed after a bounded retained-data audit with `PASS_RETAINED_TEMPORAL_SHEET_BENEFIT_NOT_IDENTIFIABLE_SCOPED`: 0/4 candidate pairs differed only in presentation ([result](https://github.com/Unjuno/agent-interface/issues/1550#issuecomment-5730971624)). This means existing retained evidence cannot isolate the effect; it does not show temporal sheets are ineffective. The audit excluded #752 and #808 from model-efficacy evidence.
- **[#1565](https://github.com/Unjuno/agent-interface/issues/1565) — assigned Rung 1 construction and matched prediction.** Open. Its live Issue records an additive path `research/observation/temporal_sheet_matched_prediction_v1/**`, model-free construction first, and model allocation still at zero. Treat that as an ownership/continuation claim to refresh before any reuse; do not enter the path or spend a model call without checking the exact branch, owner, and current allocation.
- **[#2489](https://github.com/Unjuno/agent-interface/issues/2489) — detailed matched-arm successor proposal.** Open, with no Issue comments at the 2026-10-19 read. It specifies `CURRENT_ONLY`, `SEPARATE_FRAMES_N`, and `PACKED_SHEET_N` with frozen source frames, model/prompt/session conditions, scorer, and independent audit. Its relationship to the #1565 allocation is not reconciled here.

## Keep neighboring ideas separate

- **#746 temporal frame pyramids:** whether selected historical frames help relative to a current frame. This is the value of history, not the effect of packing the same frames into one image.
- **#1028 queryable temporal buffer:** retain history locally and request a bounded historical slice later. Retrieval/queryability is separate from presentation layout.
- **#8 composite visual packing:** pack a selected set of heterogeneous views. Its selection/content question differs from a matched temporal-only packing comparison.
- **#570 model-facing visual encodings:** the broader presentation ladder and coordinate-mapping contract; it does not replace the narrower temporal-history comparison.

## Current disposition and next decision

Keep the #1525 idea in this catalog as **implemented primitive; comparative benefit unverified**. The existing record supports cataloguing the idea, but a return link and one canonical successor should be established before closing #1525 as `catalogued/deferred`. Do not close or duplicate #1565/#2489 from this note. First reconcile whether #1565's allocated construction is active and whether #2489 supersedes, extends, or duplicates it; record the chosen execution path and exact owner. Until then, run no model-facing comparison and preserve both proposals separately.

The next finite check is a read-only custody/overlap audit of #1565 and #2489: exact current branch/worktree/path owner, latest source freeze and construction result, any PR or raw evidence, and whether the preregistered arms differ. The outcome should identify one continuation path or document why both retain distinct scopes.
