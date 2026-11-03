# Current-main Calc OCR guard pair r76/r77 — 2026-11-03

## Outcome

**PASS_SCOPED:** both preregistered arms passed every task, release, dependency-join, natural-exit, container-exit, and OCR-policy gate on clean current main 673f3584c437bd9a7be0051bf111e408092bacf8.

| Arm | OCR mode | Saved cells / outer verifier | OCR calls | OCR elapsed | Compiled profile elapsed | Release / app exit / container |
|---|---|---|---:|---:|---:|---|
| r76-a4 | Predicate-scoped skip | A1=731, A2=864; verified, task_success=true | 7/17 (10 skipped) | 500.505 ms | 2282.451 ms | verified empty; natural target+launcher exit 0; container 0 |
| r77-b4 | Forced full OCR | A1=731, A2=864; verified, task_success=true | 17/17 | 1210.078 ms | 2771.61 ms | verified empty; natural target+launcher exit 0; container 0 |

For this one ordered pair, predicate-scoped OCR used 10 fewer OCR subprocesses; measured OCR time was 58.6% lower and compiled-profile elapsed time was 17.6% lower. All 14 observation dependencies joined exactly once per arm. Each arm completed two transitions with verified release. The close receipt independently records empty keys/buttons, release confirmation, owner exit 0, exact Calc/oosplash generation exit 0, and cleanup status not_needed. The parent verifier independently parsed the same FODS artifact values in each arm.

The compiled method itself returned SAFE_YIELD/effect_unavailable; the separate parent verifier established task success. These signals remain distinct.

## Conditions and limits

- Frozen order: r76-a4 skip, then r77-b4 always. One fresh Calc process and one container per arm; no retries.
- Current main source is read-only at the pinned commit. Docker Desktop 4.93.0.240920 / Engine 29.8.1, WSL cap 24 GiB / 8 CPU / 8 GiB swap / gradual reclaim. No Docker setting changed.
- Cached Debian image ID sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425; exact LibreOffice and Tesseract versions are retained in each arm.
- No model/provider/API call or token data. This measures one scripted task's OCR and compiled-profile timing, not model efficiency, price, broad speed/reliability, WSLc, MAP01, or overall computer-control completion.
- Do not pool this current-main pair with failed r73/r74 or r75: those are distinct lifecycle/source conditions. Keep Issue #57 open.

The preregistration, source freeze, exact Docker invocations, API preflight, both full raw arms, analysis, and SHA-256 manifests preserve conditions and outputs.
