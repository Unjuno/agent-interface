# Preregistration: Calc current-main task-surface stability and saved-effect gate r88-a01

Freeze: 2026-11-04, before the sole live task attempt. Base is current `main` commit `a923ab04d50a52a9f1c8e9e049c10497dca7bafa`. Attempt ID `issue57-r88-a01`; one fresh Docker/Xvfb container and one registered Calc task. No retries or replacements. The prior r87 outcome remains `FAIL_OR_UNKNOWN`; the candidate crop is informed by r87 posthoc analysis and this trial is only a prospective check of that frozen crop on one new attempt.

## Question

On current main, can the registered `calc-ocr-save-v1` path complete the fixed A1=731/A2=864 task, retain the same-frame Save effect-check receipt, and show a stable task-surface crop across the final accepted pre/post-Save observations while independently verifying the saved FODS, neutral input and clean Calc process exit?

## Frozen method and gate

Use the retained r87 public-path experiment and runner, copied into this new packet with only the attempt/schema ID changed to `issue57-r88-a01`. Preserve full 1280x800 observations. For the final two accepted compiled observations, compare the task-surface rectangle `(left=0, top=126, right=1218, bottom=742)` in RGB pixels. Right/bottom are exclusive. This rectangle is the posthoc candidate from the r87 pixel analysis; boundaries may not change after launch. Also retain and report full-frame hashes and changed-pixel count. A differing full frame is allowed only if the frozen task crop is byte-identical; otherwise this attempt fails the crop gate.

`PASS_SCOPED` requires every gate: (1) one current Calc target reviewed before input and a nonblank 1280x800 pre-input frame; (2) exactly two `enter`/`save` transitions with verified release; (3) exactly one Save `effect_checked(status=unavailable)` event, with the Save request timestamp inside the callback interval and bound to the same call, attempt, process and window generation; (4) final two observation predicates both `context_ok=true`, `cells_filled=true`, `blank=false`, plus identical frozen RGB crop; (5) pre-close independent FODS parse exact A1/A2 values 731/864; (6) close confirms no keys/buttons down and release; (7) exact Calc/launcher generation exits naturally with code 0 and clean process-group receipt; (8) post-close parent verifier returns `verified/task_success=true` for the identical artifact hash and Save request; (9) live Docker container exit 0; (10) saved evidence hashes verify. Any missing, mismatched or unknown gate yields `FAIL_OR_UNKNOWN`; no gate will be relaxed and no second attempt will be made under this freeze.

## Environment

Use only the cached image ID `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`; no pull or build. Docker Desktop Engine 29.8.1. Host `.wslconfig` is 32 GiB RAM / 12 CPUs / 16 GiB swap with gradual memory reclaim. Live container limit: 2 CPUs, 4 GiB memory and 4 GiB total memory+swap, 256 PIDs; source bind read-only; attempt evidence bind writable; disposable container root writable for exact Debian package install; Xvfb 1280x800; 600 s Python execution timeout. Runner installs LibreOffice `4:7.4.7-1+deb12u14` and Tesseract `5.3.0-2` from configured Debian mirrors; therefore only this setup phase requires container network access. No provider/model/API call, WSLc operation, MAP01, image pull/build/prune, other desktop target, or host data write is included.

## Interpretation

This is one scripted live Calc integration attempt, not an efficiency/reliability estimate. The crop was selected after inspecting r87 and will not be treated as an independently selected or broadly validated region. A successful task effect does not prove provider accounting, cold/warm/invalidation/repair economics, WSLc, MAP01, or project completion. Preserve every failed/unknown result and raw output.
