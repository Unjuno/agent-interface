# #6079 foreground-dominance adversarial control A01

Allocation `CONDITIONAL-PARALLAX-6079-FOREGROUND-A01-20261003-01`; source main `b100d9acee4ec99490b2e97066ec6af5312f1ed9`. Parent result remains immutable at `conditional_parallax_6079_t0_v1_20261003/`.

## H / T / D / C / U

- **H:** If a noncontact sham pair has unchanged target pixels but a moving, visually dominant foreground pattern that the candidate mistakes for rigid-background landmarks, the existing global landmark-centroid statistic may return a false `DISTINGUISHED` result. Without independently declared layer identity, the safe disposition should be `UNKNOWN`.
- **T:** Take only frozen sham pair 04 as the base. On a copy of one member's three post-probe PGM frames, add a 40×12 patch at the candidate's accepted landmark intensity. Do not edit any target pixels or passive frames. Set a synthetic nonzero probe receipt so the frozen candidate's movement path is exercised. Run the frozen candidate once; independently compare target pixel coordinates and compute whether the new patch alone moves the candidate's landmark centroid across its threshold.
- **D:** `CONTROL_EXPOSED` if target pixel coordinates are identical, the candidate returns `DISTINGUISHED`, and independent recomputation attributes the separation to the patch. `CONTROL_HELD` only if the candidate returns `UNKNOWN`. Malformed source or missing raw output is STOP; no retries or candidate edits.
- **C:** This adversarial layer violates the original rigid-background-only authored fixture. A positive distinction does not falsify the original finite result; it bounds where that result can transfer.
- **U:** No real imagery, camera, GUI/game, contact semantics, safety, policy, or task-effect inference. Host CPU only; standard library and frozen parent candidate, no container/model/network/GPU/shared runtime.

Formal candidate invocations before this freeze: 0. Frozen parent candidate SHA-256 `630476aec5ad0fb18a15b25749e3b804ff621423b5872ef74a2348b075627496`; parent visible corpus SHA-256 `7c2e5efe0b652344531f9cd66aad51f3385940deb00ff318fbb33fb69b4072a5`.
