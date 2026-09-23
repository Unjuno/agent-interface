# Issue #3212 — live v2 timeout/cancel terminal controls (2026-09-20)

## H/T/D/C/U

- **H (hypothesis):** The v2 receipt admission guard remains fail-closed after timeout or cancellation, while a genuinely new browser generation can still produce the intended DOM effect.
- **T (test):** Three real Docker allocations using image `mixed-formal-2992-debian:20260920`, `--network none`, Xvfb, real Chromium, X11/XTEST input, CDP DOM observation, and `/proc/<pid>/stat` process-start epochs. The v2 audit was run inside the same image.
- **D (data):** `PASS_AUDIT_V2 rows=15 controls=5 errors=0`. Each of `stale_xid`, `old_process`, `timeout_terminal`, and `cancel_terminal` has 3 rows, 0 dispatches, and 0 DOM effects. The positive new-generation control has 3 dispatches and 3 DOM effects. The raw JSONL SHA-256 is `60dcebba56e6955e815a081b81842996d205e9b848bcf3c05c9846ff575ebb24`.
- **C (conclusion):** This scoped live experiment passes: timeout/cancel terminal state is preserved by the v2 audit, while the positive new-generation control remains live. This is not a claim that all Chromium lifecycle or external-orchestrator cases are closed.
- **U (uncertainty):** External orchestrator restart and graceful restoration remain separate follow-up gates; the original and adversarial/HOLD records are intentionally unchanged.

## Reproduction

```text
docker run --rm --network none \
  -v /tmp/chromium_live3174:/audit:ro \
  --entrypoint /usr/bin/python3 mixed-formal-2992-debian:20260920 \
  /audit/audit_v2.py /audit/RAW_V2_TERMINAL_20260920.jsonl
PASS_AUDIT_V2 rows=15 controls=5 errors=0
```

The raw artifact is stored at `research/chromium/issue-3212-display-isolation-v2/terminal_raw_20260920.jsonl`.
