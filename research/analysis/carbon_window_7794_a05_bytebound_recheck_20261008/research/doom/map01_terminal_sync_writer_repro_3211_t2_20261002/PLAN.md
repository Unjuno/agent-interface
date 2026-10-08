# MAP01 terminal-sync trace-writer reproduction — T2

Status before execution: frozen, host-only synthetic child-process construction. This does not allocate or run MAP01.

## H / T / D / C / U

- **H:** The exact current-main `JsonSession` reader/writer appends a literal backslash-plus-`n` delimiter to its sidecar, so two valid child JSON events are not emitted as line-delimited JSON even though they remain structurally recoverable.
- **T:** Verify the exact source Git blob before importing it; run one synthetic child that emits exactly a `probe` event with an embedded newline value and a `terminal` event; retain the real `JsonSession` sidecar; run one independent auditor that verifies source identity, process exit, raw sidecar hash, object stream and ordinary JSONL parse failure. The candidate output path must not exist before the run. No game, model, GUI/input, Docker/OrbStack, GitHub Actions, formal recovery allocation, or retry.
- **D:** `CONFIRMED_JSONL_TRACE_FORMAT_DEFECT` iff source blob matches, child exits 0, in-memory event order is exact, the raw sidecar hash is consistent, both objects are recoverable, and ordinary JSONL parsing rejects the file. Otherwise preserve the first STOP/FAIL; never rerun this path.
- **C:** This tests only the sidecar writer via a synthetic child. It does not exercise the full MAP01 recovery fallback, explain the prior timeout, or show whether a terminal event was emitted in the missing recovery arm.
- **U:** Recovery terminal cause, actual MAP01 behavior, efficacy, and live-allocation validity remain unknown. This result authorizes no formal recovery run.

## Frozen identities and execution boundary

- Main at freeze: `df883cbe0eb60d06f304fee321edcb572fb01e08`.
- Exact imported source: `research/doom/map01_recovery_cover_matched_v2_runner_3211_diagnostic_v2.py`, Git blob `f5caf71a743a563b7de046b82d44db7ebe49e829`.
- New evidence namespace: `research/doom/map01_terminal_sync_writer_repro_3211_t2_20261002/`.
- Candidate output: `results/t2-01/` (must be absent before candidate invocation).
- Candidate invocations: 1. Independent auditor invocations: 1. Retries: 0.
- Host-only CPU child process. Docker Desktop service is Stopped/Manual, CLI requests hang, container inventory is unknown, and this task has no transferred container lease. No attempt is made to start or restart Docker.

## Frozen local source hashes (SHA-256)

- `candidate.py`: `691F0E4500387731F934C8889A7298A42A334CC004FD75AA77F5B9D25981A5ED`
- `audit.py`: `70B82B1918CA85386D93C320A63FA6177779558687E8DB2D01BF40DAEFC7802F`
- `test_construction.py`: `05204114E886F69DDE7B6144D75ADF0EBD9110462131FF474E38B64E4DD660D4`
