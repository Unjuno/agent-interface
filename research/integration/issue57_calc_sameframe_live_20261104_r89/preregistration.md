# Preregistration: post-fix Calc current-source and saved-effect gate r89-a01

Freeze: 2026-11-04, before this single live attempt. This is a new, distinct attempt following r88-a01's safe pre-input refusal. It tests the proposed source fix on candidate branch commit `8c4de6f73789230d20c1400cb0c97ff8497d303a` (main base `a923ab04d50a52a9f1c8e9e049c10497dca7bafa`); it does not claim the fix is already on main. Attempt ID is `issue57-r89-a01`. Use one fresh Docker/Xvfb container and one registered Calc task. No retries or replacements under this freeze.

## Question

Does a successful `interface_guarded_review_window` receipt on the candidate branch synchronize its nested `review.source.sequence` with the MCP-local current-source ledger, allowing two aliases minted against that exact reviewed frame to reach the guarded compiled Calc operation, and can that registered task prove its saved effect and clean input/process lifecycle?

## Frozen method and gate

Use the r88 public-path experiment and runner with only attempt/schema IDs changed, plus an auditor with the correct one-attempt mount layout. Preserve full 1280x800 frames. For the final two accepted compiled observations compare the frozen RGB crop `(left=0, top=126, right=1218, bottom=742)`; right/bottom are exclusive. Retain full-frame hashes and changed-pixel count. This crop comes from r87 posthoc analysis and was not validated by r88 because r88 stopped before the compiled observations. This single r89 trial is its first prospective evaluation.

`PASS_SCOPED` requires every frozen audit gate: current reviewed Calc target and nonblank pre-input frame; exactly two enter/save transitions with verified release; one same-frame Save effect callback timing-bound to the request, call/attempt/process/window generations; expected final visual predicates and identical frozen crop; pre-close independent FODS exact A1=731/A2=864; neutral close/release; exact Calc/launcher clean exit code 0; post-close parent verifier for the same artifact and Save request; Docker exit code 0; and preserved audit hashes. Any missing/unknown gate is `FAIL_OR_UNKNOWN`. No thresholds are relaxed and no second attempt is permitted under this registration.

## Environment and custody

Use cached image `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`, no pull/build. Docker Engine 29.8.1, Desktop 4.93.0. Host `.wslconfig`: 24 GiB RAM, 12 processors, 8 GiB swap, gradual reclaim. Live container: 2 CPUs, 4 GiB memory, 4 GiB total memory+swap, 256 PIDs. Bind source read-only and only this packet writable. Exact Debian LibreOffice `4:7.4.7-1+deb12u14` and Tesseract `5.3.0-2` apt setup uses bridge networking; no provider/model/API use, WSLc, MAP01, image pull/build/prune, other desktop target, or host data write. `run-live.ps1` captures stdout and Docker's exit code immediately after the sole `docker run`, even on nonzero exit. `run-audit.ps1` separately records the offline audit container exit. The Docker container remains `--rm`; no daemon event is needed for the exit receipt.

## Interpretation

A `PASS_SCOPED` is one candidate-branch Calc trial only. It does not prove efficiency, broad reliability, WSLc, MAP01, integrated recovery, or project completion. The live attempt runs only after this preregistration, source freeze, syntax/preflight checks, and hashes are finalized.

