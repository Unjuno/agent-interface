# Visual-context-staleness A01 result

The one frozen WSLc run passed both cases. The actual retained sequence 2→3 pair has different decoded RGB identities but identical health/ammo (97/48) and pointer binding. In the changed-frame arm, the current-main paired-signal monitor returned no invalidation, the synthetic pending answer remained eligible, and current-main final action admission returned `READY_FOR_FRESH_EXECUTOR_ADMISSION`. The same-hash control produced the same outcome.

This establishes only that the selected current-main monitor/admission boundary does not use image identity as a semantic invalidation predicate. It does not show that the frame change was a threat, that the stale answer would be wrong, or that executor input should be rejected. Both cases retained `executor_admission=null` and `input_authority_admitted=false`.

Disposition: `PASS_BOUNDARY_CHARACTERIZATION; HOLD_LIVE_SEMANTIC_EFFECT`. A future live threat allocation should capture whether an image-only scene change makes a pending policy inappropriate, how to detect that change without false interruptions, and the result of any bounded replan/recovery. No such allocation was run here. Original V39 controller source was not bound to current main; only the monitor/adapter/action-gate implementation under test is exact current main.

WSLc warned that memory was limited without swap because swap cgroups were unavailable. No resource-enforcement claim.

## Post-run audit correction

The original `audit_visual_context.py` and frozen WSLc result are retained unchanged. A follow-up audit (`audit_visual_context_v2.py`) independently decodes both retained PNGs to RGB bytes and recomputes the pixel digests, then parses the `VISUAL_CHANGED` and `VISUAL_CONTROL` records from the frozen WSLc transcript and requires exact equality with `results/result.json`. This closes the earlier audit's reliance on copied digest fields and an unbound structured result. The corrected local reproduction test writes its runtime prompt to a temporary directory; it does not overwrite the frozen `prompt.txt`. The follow-up is post-run construction/audit only and is not a second WSLc or game allocation.
