# Preregistration: finite Calc surface-readiness sampling and saved-effect gate r91-a01

Freeze: 2026-11-04, before the sole live attempt. R90 safely refused before input because the first reviewed Calc frame was mostly unrendered (660 unique colors, 0.97625 dominant fraction); r89 passed the same gate after a fixed 1-second delay. R91 tests whether a bounded observation-only readiness sampler handles this variability without imposing a longer fixed wait on already-ready frames. Candidate implementation source is `8c4de6f73789230d20c1400cb0c97ff8497d303a` from the PR branch; exact relevant source hashes are in `source-freeze.json`. Attempt ID `issue57-r91-a01`. One registered task, no input replay, no trial retry.

## Frozen readiness algorithm

After Calc launch, wait 1.0 second and review the exact discovered XID. Compute the existing nonblank gate (1280x800, at least 1,500 unique RGB colors, dominant fraction below 0.90). If it fails, take at most four additional fresh `interface_guarded_review_window` observations, 250ms apart. Every sample is retained. All samples must report the same XID, process generation, and window generation. A changed or invalid generation stops before input. Only the latest successful review frame may ground aliases and compiled input. If all five samples fail, close and record refusal; send no task input. No threshold may be relaxed, no old alias may be reused, and no sixth sample is allowed. The frozen auditor independently reads every saved review sample, verifies source sequence and XID/process/window generation continuity, rehashes its PNG, and recalculates the RGB color-count and dominant-fraction thresholds.

## Task and acceptance gate

One Calc task uses A1=731 and A2=864. `PASS_SCOPED` requires every frozen auditor gate: readiness; exactly two enter/save transitions with verified releases; same-frame Save effect callback/request timing bound to call/attempt/process/window generation; expected final predicates and identical crop `(0,126)-(1218,742)`; pre-close independent FODS parse exact values; neutral close; clean exact Calc generation exit; post-close parent verification; Docker exit 0; and preserved hashes. Any false/unknown gate is `FAIL_OR_UNKNOWN`. The first successful readiness sample is used immediately; later samples occur only after a failed nonblank check. Maximum added wait is 1.0 second.

## Environment and interpretation

Use cached image `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`, no pull/build. Docker Engine 29.8.1 / Desktop 4.93.0; host WSL limits 24 GiB RAM, 12 processors, 8 GiB swap, gradual reclaim. Container limits 2 CPUs, 4 GiB memory+swap total, 256 PIDs. Source is read-only; only this attempt packet is writable. Bridge networking is only for exact pinned Debian Calc/Tesseract package setup. No provider/model/API use, WSLc, MAP01, image pull/build/prune, other desktop target, or host data write. LF-only runner is byte-checked; host PowerShell captures Docker exit code after the sole run.

This is one candidate-branch Xvfb trial, not a speedup or broad reliability estimate. It does not establish WSLc, MAP01, integrated recovery, or project completion.

