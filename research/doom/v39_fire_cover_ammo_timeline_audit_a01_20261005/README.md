# Issue #59 — repair the retained V39 ammo-timeline auditor

## H / T / D / C / U

**H.** The published V39 fire-cover timeline auditor can accept altered saved-result fields that it does not reconstruct: ammo disposition, health endpoints, policy invalidation, model-wait duration, and active cover actions.

**T.** Recompute the original result from the SHA-pinned report and event-log Git blobs. Replay the five reported corruptions and a missing-null-field corruption against the unchanged v1 auditor. Preserve the first v2 audit, then require the exact-key A02 comparator and a separately implemented verifier to reject all six. No model, GUI, game, input, container, or live allocation is needed.

**D.** PASS for this repair only if A02 matches the unchanged result across every field and exact key set, and both A02 implementations reject all six corruptions that passed v1. Any unpinned input, mismatched original row, or missed corruption is FAIL/HOLD.

**C.** These are saved-output mutations; the omitted fields might be considered outside the narrow claim of v1's five checks. The v1 report nevertheless publishes them as reconstructed facts, so this package tests their auditability without changing the underlying observation or its interpretation.

**U.** This is a posthoc audit-integrity repair for one retained trace. It establishes no actual key hold, causal firing, safety, useful task effect, recovery benefit, survival, or MAP01 completion. It neither reruns nor upgrades the original trajectory.

## Finding

The original v1 auditor reported PASS 5/5 on six individually modified RESULT files. The raw report and event stream stayed unchanged. The first v2 auditor rejected the five published mutations but used get-based field checks, so it also passed when a null-valued invalidation field was removed. That A01 output and source are retained unchanged. A02 requires exact top-level and per-window key sets, then reconstructs each fire-cover interval's action list, wait duration, typed-observation count, ammo and health summaries, decrement count, zero exposure, and invalidation signal.

The A02 candidate matches the retained RESULT across 40 fields with no mismatch. Its independent grouped-stream verifier passes 2/2, and both A02 implementations reject all six corruptions. A01's additional null-key false pass is preserved as the reason for the A02 correction.

The historical package under v39_fire_cover_ammo_timeline_59_p01_20261005 remains byte-for-byte unchanged. A01 and A02 candidate/verifier outputs are separate additive files here.

## Scope

No formal gameplay allocation or live control run was used. The result is only whether the saved v1 summary is faithfully audited from its pinned raw inputs and whether known false-pass mutations are caught. Neither A01 nor A02 establishes physical key hold, causal firing, useful task effect, recovery efficacy, safety, or MAP01 completion.
