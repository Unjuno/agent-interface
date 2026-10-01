# #1710 Report — audit-only repair of retained #1707 XTerm evidence

**Decision: `PASS_REAL_XTERM_PHASE_OVERLAP_AUDIT_REPAIR_SCOPED`.**

The predecessor #1707 remains unchanged and retains its original `FAIL_REAL_XTERM_PHASE_OVERLAP` audit. This successor issues no X11/XTEST/task input and evaluates only the exact retained predecessor evidence.

## Repair
The sole audit change is terminal-event interpretation. #1707's runner can record:
1. the first observed `done` transition for A;
2. later, after B starts, a redundant `done_already` diagnostic because A remains terminal.

The original auditor selected the last `done|done_already`, creating 12 false `serial_order` failures. The successor uses the first terminal transition, `min(t_ns)` over those diagnostics, while leaving every other gate and threshold unchanged.

## Pinned predecessor
- raw SHA-256: `6426b6425764adc585585eff915faea504d1ddabac38ae34720660e277ce37f8`
- RESULT SHA-256: `07c44477c1e1a4ebf032ebd6443bb2bc7d8b0fab8e5a1324b7500780182946e0`
- original AUDIT SHA-256: `2fa51e9e8f4c8830a1ab101d37922f1a3bd7272d3932ff4667402c562006ed75`
- schedule SHA-256: `a87aee9a7eb3194b950c41f85a210683c4b7321767357b125ec595544fb50cd8`
- predecessor main commit: `cd90c0bcbeb6e18318a4932e9c1e8e058c105390`

All identities matched before evaluation. The original failure signature also matched exactly: 12 `serial_order:*` entries and no other original audit error class.

## Corrected independent audit
All four arms retain exactly six cases. Every case ends with no keyboard key pressed and both windows identify as XTerm. The three correctness arms end A_DONE/B_DONE; the unsafe shared-file overlap arm ends B_DONE/B_DONE in 6/6, preserving the negative control.

Using the first terminal transition:
- every serial case has A terminal before B input begins;
- every overlap case has B_STARTED before A terminal;
- every independent STARTED→DONE tail remains within the frozen [120,250] ms interval;
- serial-independent median remains 320.8507305 ms;
- overlap-independent median remains 168.087279 ms;
- reduction remains 152.7634515 ms;
- overlap/serial ratio remains 0.5238799947.

Corrected audit errors: 0. Audit invocation1; reruns0; tuning0.

## Interpretation
The real-XTerm transfer is therefore supported by a successor audit: one serialized keyboard need not force whole-intent serialization when post-input tails are independent, while a hidden shared resource correctly invalidates overlap. The evidence also reinforces the stricter rule from #1688/#23: `surface_id` is insufficient; phase resource reads/writes and dependencies must be represented explicitly.

## Limits
No new samples were added. Scope remains Linux/Xvfb/XTEST, XTerm(398), bash, one 150 ms delayed effect and one shared-file negative control. No model/token/human-tempo/cross-platform/production-runtime claim follows.
