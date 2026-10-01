# Recovery review: Issue #4032 key-state/effect cardinality

## Disposition

Recover the completed, frozen 20-case X11/Tk allocation and its lossless raw archive from the stale branch into current `main`. The formal allocation is consumed. No live X11 input, construction runner, or supervisor is rerun here.

## H/T/D/C/U

- **H:** Completed down requests, logical key-state transitions, native key events, and application text effects are distinct quantities; duplicate-down and repeat-enabled long-hold cases can make them diverge.
- **T:** Verify the six published archive parts against `ARTIFACTS.json`, assemble and verify the exact archive digest, validate all 115 archived member hashes, replay the retained raw-only audit, run four audit unit tests, and exercise twelve semantic corruption controls. These are reproduction checks over retained evidence, not a new live allocation.
- **D:** `PASS_KEY_STATE_EFFECT_CARDINALITY_BOUNDARY_SCOPED`; formal rows 20/20; duplicate-downs produced one sampled UP-to-DOWN and one inserted character, two taps produced two, and repeat-enabled long hold inserted more than one (observed 10). Replay audit: 1,872 checks, zero integrity errors, zero scientific-gate failures; controls rejected 12/12.
- **C:** The archived auditor is separately structured but from the same author, not independent human review. Scope is the measured Linux/X11/Tk fixture and ASCII-letter application boundary only.
- **U:** No full InputOwner/runtime/planner path, alternate layouts/IME, broad applications, physical-device edge, model benefit, latency benefit, production behavior, or timeout-fault injection is established. No Docker/OrbStack replication is claimed.

## Byte and local verification

All six archive chunks matched their declared lengths and SHA-256; assembled archive was 36,740 bytes with SHA-256 `ad0be00c312d5cca1714ab4b0f6d2d54b59e8619b2ea9088dc0a01cf6b8b636e`. All 115 member checks passed. The replay auditor returned `PASS_KEY_STATE_EFFECT_CARDINALITY_BOUNDARY_SCOPED`; four unit tests passed; twelve corruption controls rejected. No consumed formal case was repeated.

## Integration boundary

All recovered material stays under `research/integration/x11_key_effect_cardinality_v1/`. Historical construction failure, formal raw rows, audit history, and scope limitations are preserved. The original branch is removable only after PR checks pass, the recovered file blobs are confirmed on `main`, and no open PR still uses that branch.
