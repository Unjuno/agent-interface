# Current-main Calc same-frame live check — r87-c11

One fresh Calc/Xvfb task ran on current main `cf3ddf2f8ef44f78fac3cfed78df2904aa596691` with pinned image `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425` and Docker Engine 29.8.1. No provider/model call. Full conditions are frozen in [preregistration](preregistration.md); source and script hashes are in [source-freeze](source-freeze.json); the retained attempt outputs and per-file hash manifest are under [r87-c11](r87-c11/). A later custody audit found seven listed log files absent and one unrecovered source-script mismatch; see the [custody follow-up](../issue57_r87_custody_correction_20261104/WINDOWS_CHECKOUT_FOLLOWUP_20261104.md).

## Result: FAIL_OR_UNKNOWN under the preregistered full-frame digest gate

The run exited 0. Both `enter` and `save` transitions have verified release. The same-frame Save callback recorded `effect_checked(status=unavailable)` within its timing window. Exactly one Save request is joined to the call and process/window generations. Independent pre-close and parent post-close verification both report A1=731 and A2=864 with matching FODS SHA-256 `20514fa067adcfc8a421f4586ed83ece7788c6a8e470c2638ee839da04e71f49`. Close reports empty input state and confirmed release; Calc, launcher, owner and process group exit cleanly.

The preregistered equal-digest gate **failed**: the last two accepted full-frame PNG digests are `5c0cb961…` (observation 13) and `bdd648e1…` (observation 18). A pixel diff found 591 changed pixels out of 1,024,000, concentrated in the top-toolbar Save icon (x=83–90,y=43–50), bottom sheet-navigation controls (x=12–84,y=760–776), a status icon (x=821–830,y=785–794), and two scrollbar pixels. The spreadsheet contents and selected cell appear unchanged in the retained screenshots; the toolbar Save icon changed visual state after saving. This explains why full-frame SHA equality is too strict for this task, but the frozen gate is not rewritten after seeing the result: this run remains FAIL_OR_UNKNOWN and does not count as a same-frame pass.

The earlier r84/r85/r86 setup failures are preserved separately: missing mounted script; apt list directory blocked by read-only root; dpkg database blocked by read-only root. r87 used a disposable writable container root while keeping source read-only and persistent output restricted to the attempt directory.

## Next useful experiment

Design a prospective effect-evidence comparison that distinguishes task-surface stability from expected save-state chrome changes. Freeze the crop/normalization and verifier timing before a new attempt, keep the raw full-frame images, and independently verify the saved artifact. Do not use this result to retroactively relax the r87 gate or rerun a consumed attempt.

This one local scripted task does not establish provider accounting, efficiency, broad reliability, WSLc, MAP01, or Issue #57 completion.

## Custody status

An additive custody audit found that the 235-entry attempt manifest is not fully present in the PR tree: seven listed logs are absent and the frozen `experiment.py` bytes are not exact. The Windows checkout also required a `-text` rule to prevent CRLF conversion of raw FODS. The precise findings and corrected offline re-audit are in [`WINDOWS_CHECKOUT_FOLLOWUP_20261104.md`](../issue57_r87_custody_correction_20261104/WINDOWS_CHECKOUT_FOLLOWUP_20261104.md) and [`issue57_r87_custody_correction_20261104/README.md`](../issue57_r87_custody_correction_20261104/README.md). The live result remains `FAIL_OR_UNKNOWN`; do not interpret this packet as complete raw custody.
