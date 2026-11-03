# Preregistration: post-close Calc OCR-pruning matched pair r76-r77

Date: 2026-11-03. New pair on current main `673f3584c437bd9a7be0051bf111e408092bacf8`. This is not a retry or replacement of the frozen failed r73/r74 pair or single r75 validation.

## Question

After current-main two-phase close ordering, does the registered fixed Calc task retain the same independently verified artifact, verified input release, and natural exact-generation exit in both OCR modes, while the predicate-scoped mode invokes OCR fewer times than forced full OCR?

## Frozen arms and order

1. **r76-a4 (A, first):** default predicate-scoped behavior. Entry context-only guards skip OCR; cell-dependent Save guards retain OCR.
2. **r77-b4 (B, second):** force OCR on every fresh guarded observation using the frozen control wrapper.

Each arm receives one new disposable container and fresh Calc generation; same task A1=731, A2=864, same image, package versions, crop/PSM/whitelist/confidence and same current-main source. Each arm runs public prepare → launch → explicit review → compiled entry/save → independent pre-close FODS parse → Ctrl+Q → close/release → parent verify. Preserve all setup, failed, timeout, or UNKNOWN outcomes. No retry, replacement, rerun, or post-hoc exclusion. Run the second arm only if Docker Engine is still responsive and the first container has exited.

## Pass gates per arm

- Pre-close independent FODS parse yields exactly A1=731 and A2=864.
- Parent verifier returns `verified` and `task_success=true` for the same registered call/artifact.
- Both compiled transitions record `release_verified=true`.
- Public close records `release_confirmed=true`, `keys_down=[]`, `buttons_down=[]`, and owner exit 0.
- Exact Calc target and oosplash generation exit naturally with code 0; parent cleanup is `not_needed` (no forced cleanup counted as clean exit).
- Guard dependency joins are complete. A skips OCR only for context-only Entry guards and retains OCR for cell-dependent Save guards; B invokes OCR for every Entry and Save guard.
- Container exits 0 before the 600-second in-container timeout.

Any failed or UNKNOWN gate fails that arm. The pair is PASS only if both arms pass. Report individual profile/OCR timings and call counts; do not treat OCR elapsed as model latency or token efficiency.

## Frozen controls and limits

- Source: clean detached worktree at current main `673f3584c437bd9a7be0051bf111e408092bacf8`; source is mounted read-only.
- Image: cached `agent-interface-xvfb-mcp:late-input-r19`, exact ID `sha256:bd191d30ea94871a1d3ca717252cd07a276e8ef7d1bcb4a130b63935ce075425`; `--pull=never`.
- Host: Docker Engine 29.8.1; Docker Desktop 4.93.0.240920; WSL2 limit 8 CPU / 24 GiB RAM / 8 GiB swap / gradual reclaim. No Docker settings are changed.
- Each container: 2 CPU, 4 GiB memory and swap, 256 PIDs, `local` logging; one read-only source mount and one writable evidence mount; no published ports; `timeout --foreground --signal=TERM --kill-after=5s 600s` bounds the runner.
- The runner installs the exact preregistered Debian packages, then runs Xvfb 1280x800/Openbox and one Calc task. No model/provider/API call; no WSLc; no MAP01; no human desktop window.
- This two-arm OCR subprocess comparison is one fixed scripted task and two samples. It cannot establish provider-token savings, integrated model efficiency, price, general speed/reliability, MAP01, or project completion. Do not pool it with prior arms whose lifecycle/source conditions differ.
