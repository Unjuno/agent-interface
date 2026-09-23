# Typed HINT revalidation transferred to X11 actuation

Task: `SENSORIMOTOR-GRAPH-HINT-TRANSFER-20260917-A2`, Issue #755.

**Decision: `PASS_TYPED_HINT_TRANSFER_SCOPED`.**

## Result
A2 completed 24/24 first outcomes after A1 was retained separately as infrastructure-timeout and not pooled.

- structural-only `HINT(HISTORICAL)->ACTUATOR`, unchanged: TARGET **3/3**;
- structural-only direct HINT, moved: DECOY **3/3** (intentional unsafe negative control);
- typed direct HINT: pre-input `ACTUATOR_REQUIRES_ADMISSION_DEPENDENCY` **6/6**, backend emissions 0;
- safe `HINT->REVALIDATE_CURRENT->ADMISSION_DEPENDENCY(CURRENT)->ACTUATOR`: TARGET **12/12**, wrong clicks0;
- unchanged safe rows: `cache_hit_current_patch` **6/6**, 6,000 pixels inspected;
- moved safe rows: `fallback_full_current` **6/6**, 313,200 pixels inspected and current target center `[420,280]`;
- Button1 neutral **24/24**.

This transfers #745's static type rule into actual XTEST pointer actuation. The cache remains useful as a current-pixel-checked HINT but never grants task authority by itself.

## ERROR CHECK
Frozen audit errors0. Independent postformal verifier PASS. Seven copied-evidence corruptions rejected 7/7. Postformal source hashes remain frozen.

A1 is separately retained: 8 complete outcomes + one partial/no-result dir, `STOPPED_INFRASTRUCTURE_TIMEOUT`, not pooled.

## Limits
Synthetic X11/Tk color contract, one cached point and two layouts. Pixel counts are deterministic local-work accounting, not model cost or wall-time benefit. No general visual identity, cross-platform, model or production-security claim.
