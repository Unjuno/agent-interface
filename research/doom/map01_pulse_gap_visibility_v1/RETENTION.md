# Historical publication of the independent local pulse-gap diagnostic

Task MAP01-PULSE-GAP-VISIBILITY-20260917-001 was locally preregistered at2026-09-16T17:50:26.130962Z while GitHub writes returned Resource not found. This is POSTHOC PUBLICATION, not a remotely preregistered experiment. It was not pooled with the independently completed #649 study, and no old case was rerun.

Twelve first sessions compare six190ms Right pulses with five internal10ms versus100ms released intervals. All6 long-gap cases expose5 internal off gaps; the short arm exposes6/30 gaps (five cases merge a boundary). Long-gap yaw median84.3750deg, range84.3750..87.8906; short-gap median138.8672deg, range73.8281..138.8672. Input release/keymap and complete774 sampled tics pass. This is scoped support for game-side input segmentation, not proof of lost native key-up events or an optimal gap.

The source-rule check was POSTHOC in this predecessor. It used ViZDoom1.3.0 g_game.cpp blob33722a371dfedaf128dc0b650fac4765576a543f, five slow tics then normal turn speed and reset on off tics. All762 per-tic increments agree within8.34097591e-8deg. These residuals are arithmetic consistency, not angle-measurement uncertainty. The prospective, different-duration test is separately registered as #679; this historical result is never added to its denominator.

This continuation re-extracted the original complete archive, verified170 manifest entries and all9 frozen-source entries, and reproduced the original audit byte-identically. The original construction failure, local freeze and report remain unchanged in that archive.

Full archive filename: map01_pulse_gap_visibility_v1_evidence.tar.xz.
SHA256: 7b6ca49d0f699d4908237516bdd86612f224a871a07e18325c899bea6020f1d9.
Storage: conversation-retained original binary, NOT uploaded to this repository.
Original local report SHA256: cb001f8b8d933be6f38725c9dab6659f76aff0c496104038ff3212e5891d7801.

The GitHub numeric witness preserves all774 exact sampled tic/action/yaw values and each source result-file digest. `python verify_witness.py` performs numeric replay only; it cannot validate original timestamps,27 PNGs, input receipts or logs without the full archive. The exact binary64 yaw values are encoded using float.hex(). No native state is granted as controller input.

Conditions: AMD EPYC9V74, affinity0..4, frequency uncontrolled; CPython3.13.5/ViZDoom1.3.0; normal MAP01/skill1/35tics/s, private Xvfb/Openbox, game640x480; complete pinned offline runtime artifact522763418610ea10e57e55615fa71e76445200b9f86d208820ea97c77c234f0b. One serial session with a separate actuator/evaluator. No gameplay, survival, model efficiency or production support claim.
