# Preregistration: current-main OCR guard replication, r78–r83

Date: 2026-11-03. One local, no-provider experiment block on current main. This is a replication of the fixed scripted Calc A1=731/A2=864 workload in r76/r77, not an expanded workload suite.

## Question
Across three additional fresh matched pairs, does predicate-scoped OCR preserve exact independent task verification, input release, dependency joins, and natural app exit while reducing OCR work and elapsed time versus forced OCR? Does balancing pair order change the direction of the effect?

## Frozen order and paired blocks

| Block | First | Second | Order |
|---|---|---|---|
| 1 | r78-b5 always | r79-a5 skip | B→A |
| 2 | r80-a6 skip | r81-b6 always | A→B |
| 3 | r82-b7 always | r83-a7 skip | B→A |

Each arm uses a fresh Calc generation and disposable container. No retries, replacements, or exclusions. Proceed sequentially only if Docker is responsive and the prior container exited. Retain all failures and UNKNOWN outcomes.

## Frozen conditions and gates

Same `673f3584c437bd9a7be0051bf111e408092bacf8` source, same cached image ID, pinned LibreOffice/Tesseract packages, Xvfb 1280x800, fixed Calc profile/task, OCR crop/PSM/whitelist/confidence, 2 CPU / 4 GiB memory and swap / 256 PIDs / local logs, 600 s timeout. No models, providers, external APIs, WSLc, MAP01, or Docker setting changes. Only condition is skip context-only Entry OCR vs force OCR on every guarded observation.

Each arm must independently pass: pre-close FODS A1=731/A2=864; parent verifier `verified` and `task_success=true`; both transitions release verified; close release confirmed with no keys/buttons down and owner exit 0; exact target natural exit 0 and clean process-group exit; all 14 dependencies joined exactly once with policy-correct OCR; Docker exit 0. Any gate failure fails its arm and pair; do not discard it. Any Engine loss or unexpected remaining container ends the remaining sequence and is retained as a stopped block.

## Analysis boundary

Primary comparisons are within each frozen pair: OCR invocation count, OCR elapsed time, compiled-profile elapsed time. Report every arm, paired difference/ratio, median and range; all pairs passing their functional gates is required before considering performance. The earlier r76/r77 pair is a separate block; show it side by side, never silently pool it. This four-pair total remains a single scripted workload and cannot establish model tokens, provider-loop efficiency, price, broad speed/reliability, other apps, WSLc, MAP01, or project completion.
