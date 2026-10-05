# V39/V15 pre/post keymap A02 raw-trace reanalysis A01

## H / T / D / C / U

**H:** The preserved A02 candidate trace supports the stated two-key construction: both keycodes are down before release; the normal case has neither down after both explicit UP attempts; and the suppressed-SPACE case retains only keycode 65 after the batch. The original A02 audit's 11 failures came from joining admission and release rows together and requiring nested authority fields absent from the candidate.

**T:** Perform a raw-only secondary audit and timestamp reconciliation against the byte-preserved candidate output, run metadata, failed original audit, and frozen source snapshots from PR #7926 head `6bbdc0a70`. Derive event ordering and keymap state from the candidate trace. Do not rerun the candidate.

**D:** Preserve the original A02 `FAIL` unchanged. A secondary pass requires exact route identities, case order, pre/post key states, both UP attempts, no keymap query between UPs, telemetry-after-sample order, owner release identity/sync, and explicit no-authority fields on release rows. The first secondary audit A01 failed on an absent nested authority object; corrected A02 checks emitted row-level flags and passes 35/35.

**C:** The fake-server trace could be self-consistent but unrepresentative. XSync only establishes server synchronization. The fake keymap is not a physical keyboard or application state.

**U:** This is posthoc analysis of one already-run synthetic candidate. KeyDown events have no timestamp, so admission-to-UP is a lower bound, not exact physical key occupancy. There is no game, model, GUI, OS input, threat response, useful-feedback, bounded-recovery, or MAP01 outcome. This does not use or authorize the unassigned live-game allocation.

## Provenance and bounded work

- Base recorded by original candidate: `81a59aed13492ba1d52ea80e03d48c3d8de7b2c5`.
- Original candidate package PR head: `6bbdc0a70`.
- Fresh current main during this reanalysis: `018934cdf45fcabffcc4efe25b5c7b3d59bd459f`.
- Candidate invocations in this reanalysis: 0.
- Original auditor invocations in this reanalysis: 0.
- Secondary auditor A01: 1; retained FAIL.
- Secondary auditor A02: 1; PASS.
- Timing reconstruction: 1; four per-key rows.
- Retries: 0.
- Original source/raw/audit files are byte-copied under `inputs/pr-7926/`; new outputs are additive under `results/`.
